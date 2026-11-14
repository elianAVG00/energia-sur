[CmdletBinding()]
param(
    [string] $ArtifactDirectory = (Join-Path $env:LOCALAPPDATA 'Temp/opencode/cu05-cu06-runtime'),
    [switch] $Cleanup,
    [switch] $Rebuild,
    [string] $BackendImage = 'energia-sur-backend-checks:cu10',
    [string] $DbContainer = 'energia-sur-db-1',
    [string] $MemoryLimit = '2g'
)

<#
.SYNOPSIS
    Focused, non-destructive runner for the six historical CU05/CU06 backend tests.

.DESCRIPTION
    Provisions an isolated PostgreSQL role and test database on the existing local
    db container, creates per-run private tmpfs storage for CU05 photos and CU06
    bills, generates a synthetic CU06 confirmation secret, and runs each of the six
    historical tests individually. No shared services, persistent volumes or existing
    databases are recreated or removed. With -Cleanup, only the synthetic role and
    database created by this run are dropped.

.PARAMETER ArtifactDirectory
    Directory where per-test logs and aggregate reports are written.

.PARAMETER Cleanup
    Drop the synthetic role and database created by this run.

.PARAMETER Rebuild
    Rebuild the backend verification image before running.

.PARAMETER BackendImage
    Docker image tag to use for backend tests.

.PARAMETER DbContainer
    Name of the running PostgreSQL container.

.PARAMETER MemoryLimit
    Container memory limit (also used to disable swap for OCR privacy checks).
#>

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location (Split-Path $PSScriptRoot -Parent)

$ArtifactDirectory = (New-Item -ItemType Directory -Force -Path $ArtifactDirectory).FullName

# Only DATABASE_URL and TEST_DATABASE_URL are modified in this process.
$envKeys = @('DATABASE_URL', 'TEST_DATABASE_URL')
$previousEnv = @{}
foreach ($key in $envKeys) { $previousEnv[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }

function Restore-Environment {
    foreach ($key in $envKeys) {
        [Environment]::SetEnvironmentVariable($key, $previousEnv[$key], 'Process')
    }
}

function Invoke-Docker {
    param([string[]] $Arguments)
    & docker @Arguments
    return $LASTEXITCODE
}

try {
    # -------------------------------------------------------------------------
    # 1. Verify shared infrastructure
    # -------------------------------------------------------------------------
    $dbId = docker inspect --format '{{.Id}}' $DbContainer 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Start the documented local db ($DbContainer) before running this script."
    }
    $network = docker inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' $DbContainer 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $network) {
        throw 'Cannot resolve the local database network.'
    }

    if ($Rebuild) {
        docker build --target verification -t $BackendImage backend
        if ($LASTEXITCODE -ne 0) { throw 'Backend verification image build failed.' }
    }

    docker inspect --format '{{.Id}}' $BackendImage | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Backend image $BackendImage not found. Build it first or use -Rebuild."
    }

    # -------------------------------------------------------------------------
    # 2. Provision isolated synthetic role and database
    # -------------------------------------------------------------------------
    $suffix = [guid]::NewGuid().ToString('N').Substring(0, 12)
    $role = "cu05cu06_$suffix"
    $testDatabase = "cu05cu06_test_$suffix"
    $databasePassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    $cu06Secret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

    $sql = "CREATE ROLE $role LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '$databasePassword';`nCREATE DATABASE $testDatabase OWNER $role;"
    $provisionOutput = $sql | docker exec -i $DbContainer sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Isolated synthetic database provisioning failed.`n$provisionOutput" }

    $extSql = "CREATE EXTENSION IF NOT EXISTS vector;"
    $extOutput = $extSql | docker exec -i $DbContainer sh -c "exec psql -X -q -v ON_ERROR_STOP=1 -U `"`$POSTGRES_USER`" -d $testDatabase" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "pgvector extension provisioning failed.`n$extOutput" }
    $provisionOutput = $null
    $sql = $null

    $testUrl = "postgresql+psycopg://${role}:${databasePassword}@db:5432/${testDatabase}"
    $env:TEST_DATABASE_URL = $testUrl
    $env:DATABASE_URL = $testUrl

    # -------------------------------------------------------------------------
    # 3. Migrate the isolated database
    # -------------------------------------------------------------------------
    docker run --rm --network $network --env DATABASE_URL $BackendImage alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Test database migration failed.' }

    # -------------------------------------------------------------------------
    # 4. Verify OCR tooling and privacy preconditions
    # -------------------------------------------------------------------------
    docker run --rm --entrypoint '' $BackendImage tesseract --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Backend image is missing Tesseract.' }

    $ocrPreconditionCommand = 'import resource, pathlib; ' +
        'core_soft, _ = resource.getrlimit(resource.RLIMIT_CORE); ' +
        'swap_path = pathlib.Path("/sys/fs/cgroup/memory.swap.max"); ' +
        'swap_max = swap_path.read_text(encoding="ascii").strip() if swap_path.exists() else "missing"; ' +
        'print(f"CORE={core_soft} SWAP={swap_max}"); ' +
        'raise SystemExit(0 if core_soft == 0 and swap_max == "0" else 1)'

    $ocrCheckOutput = docker run --rm --memory $MemoryLimit --memory-swap $MemoryLimit --entrypoint '' $BackendImage python -c $ocrPreconditionCommand 2>&1
    $ocrAvailable = $LASTEXITCODE -eq 0
    $ocrCheckOutput | Out-File (Join-Path $ArtifactDirectory 'ocr-preconditions.log') -Encoding utf8

    # -------------------------------------------------------------------------
    # 5. Run each historical test in its own isolated container
    # -------------------------------------------------------------------------
    $tests = @(
        [pscustomobject]@{
            Name = 'CU06 concurrent idempotent replay and duplicate'
            Module = 'tests.test_bill_postgres.BillPostgresTests.test_concurrent_idempotent_replay_and_duplicate'
            NeedsOcr = $false
        }
        [pscustomobject]@{
            Name = 'CU06 concurrent edits advance version once'
            Module = 'tests.test_bill_postgres.BillPostgresTests.test_concurrent_edits_advance_version_once'
            NeedsOcr = $false
        }
        [pscustomobject]@{
            Name = 'CU06 bill isolation, duplicate, overlap, edit and file'
            Module = 'tests.test_bill_postgres.BillPostgresTests.test_bill_isolation_duplicate_overlap_edit_and_file'
            NeedsOcr = $false
        }
        [pscustomobject]@{
            Name = 'CU05 OCR real engine suggestion does not save'
            Module = 'tests.test_photo_postgres.PhotoPostgresTests.test_ocr_real_engine_suggestion_does_not_save'
            NeedsOcr = $true
        }
        [pscustomobject]@{
            Name = 'CU05 OCR abstains if runtime privacy is unverifiable'
            Module = 'tests.test_photo_postgres.PhotoPostgresTests.test_ocr_abstains_if_runtime_privacy_is_unverifiable'
            NeedsOcr = $false
        }
        [pscustomobject]@{
            Name = 'CU05 startup logs reconciliation failure without leaking paths'
            Module = 'tests.test_photo_postgres.PhotoPostgresTests.test_startup_logs_reconciliation_failure_without_leaking_paths'
            NeedsOcr = $false
        }
    )

    $results = [System.Collections.Generic.List[object]]::new()

    foreach ($test in $tests) {
        $safeName = ($test.Module -replace '[^A-Za-z0-9]', '_') + '.log'
        $logFile = Join-Path $ArtifactDirectory $safeName

        if ($test.NeedsOcr -and -not $ocrAvailable) {
            $ocrCheckOutput | Out-File $logFile -Encoding utf8
            "`nBLOCKED: OCR privacy preconditions are not satisfied (see ocr-preconditions.log)." | Out-File $logFile -Encoding utf8 -Append
            $results.Add([pscustomobject]@{ Test = $test.Name; Module = $test.Module; Status = 'BLOCKED'; Log = $logFile })
            continue
        }

        $runnerName = ($test.Module -replace '^tests\.', '') -replace '\.', '_' 
        $runnerPath = Join-Path $ArtifactDirectory "runner_${runnerName}.py"
        @"
import sys, os, unittest
if __name__ == '__main__':
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/tests')
    os.chdir('/app/tests')
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('$($test.Module -replace '^tests\.', '')')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
"@ | Out-File $runnerPath -Encoding utf8

        $runArgs = @(
            'run', '--rm',
            '--network', $network,
            '--memory', $MemoryLimit,
            '--memory-swap', $MemoryLimit,
            '--tmpfs', '/photo-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700',
            '--tmpfs', '/bill-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700',
            '--env', 'DATABASE_URL',
            '--env', 'TEST_DATABASE_URL',
            '--env', 'CU05_PHOTO_DIR=/photo-tests',
            '--env', 'CU06_BILL_DIR=/bill-tests',
            '--env', "CU06_CONFIRMATION_SECRET=$cu06Secret",
            '--volume', "${runnerPath}:/tmp/runner.py:ro",
            '--workdir', '/app/tests',
            $BackendImage,
            'python', '/tmp/runner.py'
        )

        $output = & docker @runArgs 2>&1
        $exit = $LASTEXITCODE
        $output | Out-File $logFile -Encoding utf8

        $status = if ($exit -eq 0) { 'PASS' } else { 'FAIL' }
        $results.Add([pscustomobject]@{ Test = $test.Name; Module = $test.Module; Status = $status; Log = $logFile })
    }

    # -------------------------------------------------------------------------
    # 6. Write aggregate report
    # -------------------------------------------------------------------------
    $reportFile = Join-Path $ArtifactDirectory 'report.txt'
    $report = @"
CU05/CU06 backend runtime results
=================================
Generated    : $(Get-Date -Format 'o')
Database     : $testDatabase
Role         : $role
Backend image: $BackendImage
OCR available: $ocrAvailable

Test results:
"@
    $report += "`n" + ($results | Format-Table -AutoSize | Out-String)
    $report += "`nArtifact directory: $ArtifactDirectory"
    $report | Out-File $reportFile -Encoding utf8
    $results | Export-Csv -Path (Join-Path $ArtifactDirectory 'results.csv') -NoTypeInformation -Encoding utf8

    Write-Output "`n$report"

    $failed = $results | Where-Object { $_.Status -eq 'FAIL' }
    if ($failed) {
        throw "One or more tests failed: $($failed.Module -join ', '). See logs in $ArtifactDirectory."
    }
}
finally {
    Restore-Environment
    if ($Cleanup -and $testDatabase -and $role) {
        $dropSql = "DROP DATABASE IF EXISTS $testDatabase; DROP ROLE IF EXISTS $role;"
        $dropSql | docker exec -i $DbContainer sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>&1 |
            Out-File (Join-Path $ArtifactDirectory 'cleanup.log') -Encoding utf8
    }
    Pop-Location
}
