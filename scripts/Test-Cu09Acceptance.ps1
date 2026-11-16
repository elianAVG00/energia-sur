[CmdletBinding()]
param(
    [string] $ArtifactDirectory = (Join-Path $env:LOCALAPPDATA 'Temp/opencode/cu09-acceptance'),
    [string] $BackendTestPattern = '',
    [string] $E2ETestPattern = '',
    [switch] $BackendOnly,
    [switch] $RunPostBrowserChecks
)

# Additive synthetic acceptance only. No databases, roles, tables or volumes are deleted.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$backendPatterns = @($BackendTestPattern -split ';' | Where-Object { $_ })
$e2ePatterns = @($E2ETestPattern -split ';' | Where-Object { $_ })
Push-Location (Split-Path $PSScriptRoot -Parent)
$keys = @('DATABASE_URL', 'TEST_DATABASE_URL', 'CU09_DATABASE_URL', 'POSTGRES_PASSWORD',
          'QA_USERNAME_A', 'QA_USERNAME_B', 'QA_USERNAME_REGISTERED', 'QA_PASSWORD', 'E2E_BASE_URL', 'CU05_PHOTO_DIR',
          'CU06_BILL_DIR', 'CU06_CONFIRMATION_SECRET', 'OUTAGE_SCHEDULER_ENABLED',
          'SCHEDULED_WORKS_SCHEDULER_ENABLED', 'ASSISTANT_GUIDE_INGEST')
    $previous = @{}
    $stageFailures = [System.Collections.Generic.List[string]]::new()
foreach ($key in $keys) { $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
try {
    New-Item -ItemType Directory -Force -Path $ArtifactDirectory | Out-Null
    $before = docker inspect --format '{{.Id}}' energia-sur-db-1
    if ($LASTEXITCODE -ne 0) { throw 'Start the documented local db before this acceptance.' }
    $network = docker inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' energia-sur-db-1
    if ($LASTEXITCODE -ne 0 -or -not $network) { throw 'Cannot resolve the local database network.' }
    $suffix = [guid]::NewGuid().ToString('N').Substring(0, 12)
    $role = "cu09_$suffix"
    $appDatabase = "cu09_app_$suffix"
    $testDatabase = "cu09_test_$suffix"
    $databasePassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    $env:QA_PASSWORD = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
    $env:QA_USERNAME_A = "qa_a_$suffix"
    $env:QA_USERNAME_B = "qa_b_$suffix"
    $env:QA_USERNAME_REGISTERED = "qa_new_$suffix"
    $env:E2E_BASE_URL = 'http://127.0.0.1:5173'
    $env:CU06_BILL_DIR = '/bill-tests'
    $env:CU06_CONFIRMATION_SECRET = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    # Password goes through stdin only; never arguments, logs or a shared file.
    $sql = "CREATE ROLE $role LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '$databasePassword';`nCREATE DATABASE $appDatabase OWNER $role;`nCREATE DATABASE $testDatabase OWNER $role;"
    $provisionOutput = $sql | docker exec -i energia-sur-db-1 sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Isolated synthetic database provisioning failed; no secret output reproduced.' }
    $provisionOutput = $null
    $sql = $null
    # The local PostgreSQL image has pgvector available, but the application role
    # is deliberately not a superuser. Install it only in these new synthetic DBs.
    foreach ($database in @($appDatabase, $testDatabase)) {
        docker exec energia-sur-db-1 sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$1" -c "CREATE EXTENSION IF NOT EXISTS vector"' sh $database
        if ($LASTEXITCODE -ne 0) { throw 'pgvector setup in an isolated synthetic database failed.' }
    }
    $env:CU09_DATABASE_URL = "postgresql+psycopg://${role}:${databasePassword}@db:5432/$appDatabase"
    $env:TEST_DATABASE_URL = "postgresql+psycopg://${role}:${databasePassword}@db:5432/$testDatabase"
    $databasePassword = $null
    $env:OUTAGE_SCHEDULER_ENABLED = 'false'
    $env:SCHEDULED_WORKS_SCHEDULER_ENABLED = 'false'
    $env:ASSISTANT_GUIDE_INGEST = 'false'
    foreach ($url in @($env:TEST_DATABASE_URL, $env:CU09_DATABASE_URL)) {
        $env:DATABASE_URL = $url
        docker run --rm --network $network --env DATABASE_URL energia-sur-backend-checks:cu09 alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Additive CU09 migration failed.' }
        # Running the same head twice must be non-destructive and idempotent.
        docker run --rm --network $network --env DATABASE_URL energia-sur-backend-checks:cu09 alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Repeated migration failed.' }
    }
    $env:DATABASE_URL = $env:TEST_DATABASE_URL
    # CU05 photo tests need a writable private directory owned by runtime UID 10001.
    # CU05/CU06 files use per-run tmpfs storage, never a persistent volume.
    $env:CU05_PHOTO_DIR = '/photo-tests'
    if ($backendPatterns.Count -gt 0) {
        foreach ($pattern in $backendPatterns) {
            docker run --rm --network $network --memory 2g --memory-swap 2g --ulimit 'core=0' --env DATABASE_URL --env TEST_DATABASE_URL --env TEST_CU04_MIGRATION=1 --env CU05_PHOTO_DIR --env CU06_BILL_DIR --env CU06_CONFIRMATION_SECRET --tmpfs '/photo-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700' --tmpfs '/bill-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700' energia-sur-backend-checks:cu09 python -m unittest discover -s tests -p $pattern -v
            if ($LASTEXITCODE -ne 0) { $stageFailures.Add("backend test pattern $pattern") }
        }
    } else {
        docker run --rm --network $network --memory 2g --memory-swap 2g --ulimit 'core=0' --env DATABASE_URL --env TEST_DATABASE_URL --env TEST_CU04_MIGRATION=1 --env CU05_PHOTO_DIR --env CU06_BILL_DIR --env CU06_CONFIRMATION_SECRET --tmpfs '/photo-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700' --tmpfs '/bill-tests:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700' energia-sur-backend-checks:cu09 python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { $stageFailures.Add('backend PostgreSQL suite') }
    }
    if ($BackendOnly) {
        if ($stageFailures.Count -gt 0) {
            throw "Backend tests failed: $($stageFailures -join ', '). Diagnostic output is retained by the caller."
        }
        Write-Output 'PASS: selected isolated backend test patterns.'
        Write-Output "Retained synthetic databases: $appDatabase and $testDatabase. No data/volume deletion."
        return
    }
    $env:DATABASE_URL = $env:CU09_DATABASE_URL
    foreach ($username in @($env:QA_USERNAME_A, $env:QA_USERNAME_B)) {
        $env:QA_PASSWORD | docker run --rm -i --network $network --env DATABASE_URL energia-sur-backend-checks:cu09 python -m app.provision --username $username --password-stdin
        if ($LASTEXITCODE -ne 0) { throw 'Synthetic account provisioning failed.' }
    }
    if (-not $env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD = 'unused-for-existing-db-no-recreation' }
    docker compose -f compose.yaml -f compose.cu09.yaml config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'CU09 Compose configuration failed.' }
    # Do not recreate the existing db or alter its initialization credentials/volume.
    docker compose -f compose.yaml -f compose.cu09.yaml up -d --no-deps --build --wait --wait-timeout 90 backend frontend
    if ($LASTEXITCODE -ne 0) { throw 'CU09 application startup failed.' }
    $qaContainer = "energia-sur-cu09-qa-$suffix"
    if ($e2ePatterns.Count -gt 0) {
        docker run --name $qaContainer --network container:energia-sur-frontend-1 --env QA_USERNAME_A --env QA_USERNAME_B --env QA_USERNAME_REGISTERED --env QA_PASSWORD --env E2E_BASE_URL energia-sur-frontend-checks:cu09 npm run test:e2e -- $e2ePatterns
    } else {
        docker run --name $qaContainer --network container:energia-sur-frontend-1 --env QA_USERNAME_A --env QA_USERNAME_B --env QA_USERNAME_REGISTERED --env QA_PASSWORD --env E2E_BASE_URL energia-sur-frontend-checks:cu09 npm run test:e2e
    }
    $browserExit = $LASTEXITCODE
    docker cp "${qaContainer}:/tmp/cu09-artifacts/." $ArtifactDirectory
    $copyExit = $LASTEXITCODE
    if ($browserExit -ne 0) { $stageFailures.Add('Playwright browser suite') }
    if ($copyExit -ne 0) { $stageFailures.Add('browser artifact collection') }
    if ($e2ePatterns.Count -gt 0 -and -not $RunPostBrowserChecks) {
        $after = docker inspect --format '{{.Id}}' energia-sur-db-1
        if ($LASTEXITCODE -ne 0 -or $before -ne $after) { throw 'Unexpected original database recreation.' }
        if ($stageFailures.Count -gt 0) {
            throw "Acceptance stages failed: $($stageFailures -join ', '). Synthetic artifacts were retained."
        }
        Write-Output 'PASS: selected synthetic browser acceptance and unchanged original db container.'
        Write-Output "Retained synthetic databases: $appDatabase and $testDatabase. QA container: $qaContainer. No data/volume deletion."
        Write-Output "Synthetic-only browser artifacts: $ArtifactDirectory"
        return
    }
    $closedPdf = Join-Path $ArtifactDirectory 'closed.pdf'
    $ongoingPdf = Join-Path $ArtifactDirectory 'ongoing.pdf'
    if (-not (Test-Path $closedPdf) -or -not (Test-Path $ongoingPdf)) {
        $stageFailures.Add('CU09 downloaded PDF artifacts unavailable')
    } else {
        docker run --rm --mount "type=bind,source=$ArtifactDirectory,target=/evidence,readonly" energia-sur-backend-checks:cu09 python -c "from pypdf import PdfReader; a=' '.join(p.extract_text() for p in PdfReader('/evidence/closed.pdf').pages); b=' '.join(p.extract_text() for p in PdfReader('/evidence/ongoing.pdf').pages); assert all(x in a for x in ['Álvarez','Observación sintética de energía','TEST-001','3 h 0 min','2026-11-01 00:00','2026-11-02 00:00']); assert a.count('Cerrado')==2 and a.index('2026-11-01 11:00')<a.index('2026-11-01 10:00'); assert b.count('En curso')==2 and '13 h 0 min' in b; print('PASS: actual downloaded PDF text, Unicode, complete fields, row order, statuses and totals')"
        if ($LASTEXITCODE -ne 0) { $stageFailures.Add('CU09 PDF content assertions') }
    }
    docker run --rm --network $network --env DATABASE_URL energia-sur-backend-checks:cu09 alembic upgrade head
    if ($LASTEXITCODE -ne 0) { $stageFailures.Add('repeated migration after integration data') }
    docker restart energia-sur-backend-1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $stageFailures.Add('backend restart') }
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Invoke-WebRequest 'http://127.0.0.1:5173/api/health' -TimeoutSec 3
            if ($health.StatusCode -eq 200 -and $health.Content -eq '{"status":"ok"}') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) {
        $stageFailures.Add('backend proxy health after restart')
    } elseif (Test-Path (Join-Path $ArtifactDirectory 'state.json')) {
        try {
            $webSession = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
            $loginBody = @{username=$env:QA_USERNAME_A; password=$env:QA_PASSWORD} | ConvertTo-Json -Compress
            $loginResponse = Invoke-WebRequest 'http://127.0.0.1:5173/api/login' -Method Post -ContentType 'application/json' -Body $loginBody -Headers @{Origin=$env:E2E_BASE_URL} -WebSession $webSession
            if ($loginResponse.StatusCode -ne 200) { throw 'Synthetic login failed.' }
            # Normalize the API array before checking the saved synthetic domicile.
            $homes = Invoke-RestMethod 'http://127.0.0.1:5173/api/domiciles' -WebSession $webSession
            $saved = Get-Content (Join-Path $ArtifactDirectory 'state.json') -Raw | ConvertFrom-Json
            if (-not (@($homes) | Where-Object { $_.id -eq $saved.domicile })) { throw 'Synthetic domicile missing.' }
            $records = Invoke-RestMethod "http://127.0.0.1:5173/api/domiciles/$($saved.domicile)/interruptions" -WebSession $webSession
            if (@($records).Count -ne 3) { throw 'Synthetic diary count mismatch.' }
            foreach ($record in $records) {
                $original = @($saved.cuts | Where-Object { $_.id -eq $record.id })
                if ($original.Count -ne 1) { throw 'Synthetic record identity mismatch.' }
                foreach ($field in @('domicile_id','start_at','end_at','observations','complaint_number','version','status')) {
                    if ($record.$field -ne $original[0].$field) { throw 'Synthetic record changed after restart.' }
                }
            }
            if (Test-Path (Join-Path $ArtifactDirectory 'registration-state.json')) {
                $registrationState = Get-Content (Join-Path $ArtifactDirectory 'registration-state.json') -Raw | ConvertFrom-Json
                $registeredLoginBody = @{
                    username = $registrationState.username
                    password = $env:QA_PASSWORD
                } | ConvertTo-Json -Compress
                $registeredSession = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
                $registeredLogin = Invoke-WebRequest 'http://127.0.0.1:5173/api/login' -Method Post -ContentType 'application/json' -Body $registeredLoginBody -Headers @{Origin=$env:E2E_BASE_URL} -WebSession $registeredSession
                if ($registeredLogin.StatusCode -ne 200) { throw 'Registered synthetic account did not persist.' }
                $registeredHomes = Invoke-RestMethod 'http://127.0.0.1:5173/api/domiciles' -WebSession $registeredSession
                if (-not (@($registeredHomes) | Where-Object { $_.id -eq $registrationState.domicile })) {
                    throw 'Registered account domicile did not persist.'
                }
            } else {
                $stageFailures.Add('registered-account persistence state unavailable')
            }
            if (Test-Path (Join-Path $ArtifactDirectory 'cu05-state.json')) {
                $cu05 = Get-Content (Join-Path $ArtifactDirectory 'cu05-state.json') -Raw | ConvertFrom-Json
                if (-not (@($homes) | Where-Object { $_.id -eq $cu05.domicile })) { throw 'Synthetic CU05 domicile missing.' }
                $readings = Invoke-RestMethod "http://127.0.0.1:5173/api/meters/$($cu05.meter)/readings" -WebSession $webSession
                $reading = @($readings | Where-Object { $_.id -eq $cu05.reading })
                if ($reading.Count -ne 1 -or $reading[0].value_kwh -ne '12345' -or $reading[0].has_photo -ne $true) {
                    throw 'Synthetic reading did not persist.'
                }
                $photo = Invoke-WebRequest "http://127.0.0.1:5173/api/meters/$($cu05.meter)/readings/$($cu05.reading)/photo" -WebSession $webSession
                if ($photo.StatusCode -ne 200 -or $photo.RawContentLength -le 0) { throw 'Synthetic photo did not persist.' }
                if ([string]$photo.Headers['Content-Type'] -ne 'image/png' -or [string]$photo.Headers['X-Content-Type-Options'] -ne 'nosniff') {
                    throw 'Synthetic photo headers changed.'
                }
            }
        } catch {
            $stageFailures.Add('synthetic account/domicile/diary persistence assertions')
        }
    } else {
        $stageFailures.Add('restart persistence state artifact unavailable')
    }
    $after = docker inspect --format '{{.Id}}' energia-sur-db-1
    if ($LASTEXITCODE -ne 0 -or $before -ne $after) { $stageFailures.Add('original database container identity') }
    if ($stageFailures.Count -gt 0) {
        throw "Acceptance stages failed: $($stageFailures -join ', '). Synthetic databases/artifacts retained; no data or volume deletion."
    }
    Write-Output 'PASS: migrated PostgreSQL suite, real browser workflow, account isolation, downloaded PDFs, account/domicile/diary persistence after backend restart, exact health and unchanged original db container.'
    Write-Output "Retained synthetic databases: $appDatabase and $testDatabase. QA container: $qaContainer. No data/volume deletion."
    Write-Output "Synthetic-only PDF artifacts: $ArtifactDirectory"
}
finally {
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process') }
    Pop-Location
}
