[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location (Split-Path $PSScriptRoot -Parent)
$backendStopped = $false
try {
    function Assert-Health([string] $Uri) {
        $response = Invoke-WebRequest -Uri $Uri -TimeoutSec 10
        $json = $response.Content | ConvertFrom-Json
        if ($response.StatusCode -ne 200 -or $json.status -ne 'ok' -or @($json.PSObject.Properties).Count -ne 1) {
            throw "Unexpected health contract from $Uri"
        }
        Write-Output "PASS: $Uri HTTP 200 with expected health JSON."
    }

    Assert-Health 'http://127.0.0.1:8000/health'
    Assert-Health 'http://127.0.0.1:5173/api/health'
    $backendStopped = $true
    docker compose stop backend
    if ($LASTEXITCODE -ne 0) { throw 'Could not stop backend for failure verification.' }
    $proxyFailed = $false
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5173/api/health' -TimeoutSec 10 -SkipHttpErrorCheck
        $proxyFailed = $response.StatusCode -ge 400
    }
    catch [System.Net.Http.HttpRequestException] { $proxyFailed = $true }
    catch [System.Threading.Tasks.TaskCanceledException] { $proxyFailed = $true }
    if (-not $proxyFailed) { throw 'Proxy unexpectedly succeeded while backend was stopped.' }
    Write-Output 'PASS: real proxy fails while backend is stopped.'
}
finally {
    try {
        if ($backendStopped) {
            docker compose up -d --no-deps --wait --wait-timeout 90 backend
            if ($LASTEXITCODE -ne 0) { throw 'Backend restoration failed; restore it manually.' }
            Assert-Health 'http://127.0.0.1:5173/api/health'
        }
    }
    finally { Pop-Location }
}
Write-Output 'UI ACCEPTANCE PENDING: this script checks HTTP/proxy only. Follow the README browser steps.'
