# Stop dev observability stack

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Stopping observability stack..." -ForegroundColor Cyan
docker compose -f "$Root\docker-compose.observability.yml" down

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to stop observability stack." -ForegroundColor Red
    exit 1
}

Write-Host "Observability stack stopped." -ForegroundColor Green
