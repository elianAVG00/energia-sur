[CmdletBinding()]
param(
    [string] $ArtifactDirectory = (Join-Path $env:LOCALAPPDATA 'Temp/opencode/cu09-acceptance')
)

# Additive synthetic acceptance only. No databases, roles, tables or volumes are deleted.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location (Split-Path $PSScriptRoot -Parent)
$keys = @('DATABASE_URL', 'TEST_DATABASE_URL', 'CU09_DATABASE_URL', 'POSTGRES_PASSWORD',
          'QA_USERNAME_A', 'QA_USERNAME_B', 'QA_PASSWORD', 'E2E_BASE_URL', 'CU05_PHOTO_DIR')
$previous = @{}
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
    $env:E2E_BASE_URL = 'http://127.0.0.1:5173'
    # Password goes through stdin only; never arguments, logs or a shared file.
    $sql = "CREATE ROLE $role LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '$databasePassword';`nCREATE DATABASE $appDatabase OWNER $role;`nCREATE DATABASE $testDatabase OWNER $role;"
    $provisionOutput = $sql | docker exec -i energia-sur-db-1 sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Isolated synthetic database provisioning failed; no secret output reproduced.' }
    $provisionOutput = $null
    $sql = $null
    $env:CU09_DATABASE_URL = "postgresql+psycopg://${role}:${databasePassword}@db:5432/$appDatabase"
    $env:TEST_DATABASE_URL = "postgresql+psycopg://${role}:${databasePassword}@db:5432/$testDatabase"
    $databasePassword = $null
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
    # A per-run tmpfs keeps synthetic objects out of every persistent volume.
    $env:CU05_PHOTO_DIR = '/photo-tests'
    docker run --rm --network $network --env DATABASE_URL --env TEST_DATABASE_URL --env TEST_CU04_MIGRATION=1 --env CU05_PHOTO_DIR --tmpfs '/photo-tests:rw,nosuid,nodev,size=32m,uid=10001,gid=10001,mode=700' energia-sur-backend-checks:cu09 python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Backend PostgreSQL acceptance failed.' }
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
    docker run --name $qaContainer --network container:energia-sur-frontend-1 --env QA_USERNAME_A --env QA_USERNAME_B --env QA_PASSWORD --env E2E_BASE_URL energia-sur-frontend-checks:cu09 npm run test:e2e
    $browserExit = $LASTEXITCODE
    docker cp "${qaContainer}:/tmp/cu09-artifacts/." $ArtifactDirectory
    if ($LASTEXITCODE -ne 0 -or $browserExit -ne 0) { throw 'Browser acceptance failed; retained QA container and local artifacts for diagnosis.' }
    docker run --rm --mount "type=bind,source=$ArtifactDirectory,target=/evidence,readonly" energia-sur-backend-checks:cu09 python -c "from pypdf import PdfReader; a=' '.join(p.extract_text() for p in PdfReader('/evidence/closed.pdf').pages); b=' '.join(p.extract_text() for p in PdfReader('/evidence/ongoing.pdf').pages); assert all(x in a for x in ['Álvarez','Observación sintética de energía','TEST-001','3 h 0 min','2026-11-01 00:00','2026-11-02 00:00']); assert a.count('Cerrado')==2 and a.index('2026-11-01 11:00')<a.index('2026-11-01 10:00'); assert b.count('En curso')==2 and '13 h 0 min' in b; print('PASS: actual downloaded PDF text, Unicode, complete fields, row order, statuses and totals')"
    if ($LASTEXITCODE -ne 0) { throw 'Downloaded PDF inspection failed.' }
    docker run --rm --network $network --env DATABASE_URL energia-sur-backend-checks:cu09 alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Repeated migration with persisted diary data failed.' }
    docker restart energia-sur-backend-1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Backend restart failed.' }
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $health = Invoke-WebRequest 'http://127.0.0.1:5173/api/health' -TimeoutSec 3
            if ($health.StatusCode -eq 200 -and $health.Content -eq '{"status":"ok"}') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw 'Backend did not recover its exact proxy health contract.' }
    $webSession = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
    $loginBody = @{username=$env:QA_USERNAME_A; password=$env:QA_PASSWORD} | ConvertTo-Json -Compress
    $loginResponse = Invoke-WebRequest 'http://127.0.0.1:5173/api/login' -Method Post -ContentType 'application/json' -Body $loginBody -Headers @{Origin=$env:E2E_BASE_URL} -WebSession $webSession
    if ($loginResponse.StatusCode -ne 200) { throw 'Login after restart failed.' }
    # Invoke-RestMethod emits a JSON array as one pipeline object. Assign first,
    # then normalize; wrapping the command itself creates a nested one-item array.
    $homes = Invoke-RestMethod 'http://127.0.0.1:5173/api/domiciles' -WebSession $webSession
    $saved = Get-Content (Join-Path $ArtifactDirectory 'state.json') -Raw | ConvertFrom-Json
    # CU04 browser specs share this synthetic account; require the saved domicile, not a count.
    if (-not (@($homes) | Where-Object { $_.id -eq $saved.domicile })) { throw 'Saved domicile did not persist across restart.' }
    $records = Invoke-RestMethod "http://127.0.0.1:5173/api/domiciles/$($saved.domicile)/interruptions" -WebSession $webSession
    if (@($records).Count -ne 3) { throw 'Three diary records did not persist across restart.' }
    foreach ($record in $records) {
        $original = @($saved.cuts | Where-Object { $_.id -eq $record.id })
        if ($original.Count -ne 1) { throw 'Stored record identity changed across restart.' }
        foreach ($field in @('domicile_id','start_at','end_at','observations','complaint_number','version','status')) {
            if ($record.$field -ne $original[0].$field) { throw 'Stored corrected/closed record changed across restart.' }
        }
    }
    # CU05: the browser saved a manual reading with a synthetic private photo.
    $cu05 = Get-Content (Join-Path $ArtifactDirectory 'cu05-state.json') -Raw | ConvertFrom-Json
    if (-not (@($homes) | Where-Object { $_.id -eq $cu05.domicile })) { throw 'CU05 domicile did not persist across restart.' }
    $readings = Invoke-RestMethod "http://127.0.0.1:5173/api/meters/$($cu05.meter)/readings" -WebSession $webSession
    $reading = @($readings | Where-Object { $_.id -eq $cu05.reading })
    if ($reading.Count -ne 1) { throw 'CU05 reading did not persist across restart.' }
    if ($reading[0].value_kwh -ne '12345' -or $reading[0].has_photo -ne $true) { throw 'CU05 reading value or photo link changed across restart.' }
    $photo = Invoke-WebRequest "http://127.0.0.1:5173/api/meters/$($cu05.meter)/readings/$($cu05.reading)/photo" -WebSession $webSession
    if ($photo.StatusCode -ne 200 -or $photo.RawContentLength -le 0) { throw 'CU05 private photo did not persist across restart.' }
    if ([string]$photo.Headers['Content-Type'] -ne 'image/png') { throw 'CU05 private photo content type changed across restart.' }
    if ([string]$photo.Headers['X-Content-Type-Options'] -ne 'nosniff') { throw 'CU05 private photo lost its nosniff header.' }
    $after = docker inspect --format '{{.Id}}' energia-sur-db-1
    if ($LASTEXITCODE -ne 0 -or $before -ne $after) { throw 'Unexpected original database recreation.' }
    Write-Output 'PASS: migrated PostgreSQL tests, real browser workflow, five-action isolation, downloaded PDFs, restart persistence, exact health, private CU05 reading/photo restart persistence and unchanged original db container.'
    Write-Output "Retained synthetic databases: $appDatabase and $testDatabase. QA container: $qaContainer. No data/volume deletion."
    Write-Output "Synthetic-only PDF artifacts: $ArtifactDirectory"
}
finally {
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process') }
    Pop-Location
}
