# Start dev observability stack (Jaeger + OTel Collector)
# Requires Docker Desktop

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternatives without Docker:" -ForegroundColor Yellow
    Write-Host "  OTEL_ENABLED=true"
    Write-Host "  OTEL_CONSOLE_EXPORTER=true"
    Write-Host ""
    Write-Host "Then run: python scripts/verify_observability.py"
    exit 1
}

Write-Host "Starting observability stack..." -ForegroundColor Cyan
docker compose -f "$Root\docker-compose.observability.yml" up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start observability stack." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Observability stack is running." -ForegroundColor Green
Write-Host "  Jaeger UI:  http://localhost:16686"
Write-Host "  OTLP gRPC:  localhost:4317"
Write-Host ""
Write-Host "Add to .env:" -ForegroundColor Yellow
Write-Host "  OTEL_ENABLED=true"
Write-Host "  OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317"
Write-Host ""
Write-Host "Install Python packages:" -ForegroundColor Yellow
Write-Host "  pip install -r requirements-observability.txt"
