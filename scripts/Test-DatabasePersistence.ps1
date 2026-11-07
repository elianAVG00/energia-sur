[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    function Get-DatabaseIdentity {
        $containerId = docker compose ps -q db
        if ($LASTEXITCODE -ne 0 -or -not $containerId) {
            throw 'Cannot identify the running database container.'
        }
        $volumeName = docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql"}}{{.Name}}{{end}}{{end}}' $containerId
        if ($LASTEXITCODE -ne 0 -or -not $volumeName) {
            throw 'Cannot identify the PostgreSQL named volume.'
        }
        return [pscustomobject]@{ Container = "$containerId".Trim(); Volume = "$volumeName".Trim() }
    }

    function Invoke-DatabaseSql([string] $Sql) {
        # Resolve only non-secret names within the container; never print credentials.
        $result = $Sql | docker compose exec -T db sh -c 'exec psql -X -v ON_ERROR_STOP=1 -A -t -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
        if ($LASTEXITCODE -ne 0) {
            throw 'psql failed; database acceptance did not pass.'
        }
        return @($result | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    }

    $before = Get-DatabaseIdentity
    $selectOne = @(Invoke-DatabaseSql 'SELECT 1;')
    if ($selectOne.Count -ne 1 -or $selectOne[0] -ne '1') {
        throw 'SELECT 1 did not return exactly 1.'
    }
    $marker = [guid]::NewGuid().ToString()
    $null = Invoke-DatabaseSql "CREATE SCHEMA IF NOT EXISTS environment_acceptance; CREATE TABLE IF NOT EXISTS environment_acceptance.persistence (marker text PRIMARY KEY); INSERT INTO environment_acceptance.persistence(marker) VALUES ('$marker');"
    $readBefore = @(Invoke-DatabaseSql "SELECT marker FROM environment_acceptance.persistence WHERE marker = '$marker';")
    if ($readBefore.Count -ne 1 -or $readBefore[0] -ne $marker) {
        throw 'Synthetic marker was not committed before recreation.'
    }

    # Preserve pgdata. No volume removal, seed rerun, or marker reinsertion.
    docker compose up -d --no-deps --force-recreate --wait --wait-timeout 90 db
    if ($LASTEXITCODE -ne 0) {
        throw 'Database recreation/readiness failed.'
    }
    $after = Get-DatabaseIdentity
    if ($before.Container -eq $after.Container -or $before.Volume -ne $after.Volume) {
        throw 'Expected a new database container using the same named volume.'
    }
    $readAfter = @(Invoke-DatabaseSql "SELECT marker FROM environment_acceptance.persistence WHERE marker = '$marker';")
    if ($readAfter.Count -ne 1 -or $readAfter[0] -ne $marker) {
        throw 'The original synthetic marker did not survive recreation.'
    }
    Write-Output "PASS: SELECT 1; marker $marker survived db recreation."
    Write-Output "Container before: $($before.Container)"
    Write-Output "Container after:  $($after.Container)"
    Write-Output "Preserved volume: $($after.Volume)"
}
finally {
    Pop-Location
}
