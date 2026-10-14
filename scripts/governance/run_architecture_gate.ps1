# ═══════════════════════════════════════════════════════════════════════════════
# E-CÜZDAN EAFGS — Architecture & Repository Health Gate Runner
# ═══════════════════════════════════════════════════════════════════════════════
param (
    [string]$Mode = "WARNING"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Running E-Cüzdan EAFGS Architecture & Repository Health Gate" -ForegroundColor Cyan
Write-Host " Mode: $Mode" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$env:EAFGS_MODE = $Mode
python scripts/governance/architecture_gate.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nArchitecture Gate Completed Successfully." -ForegroundColor Green
} else {
    Write-Host "`nArchitecture Gate Failed with Blocking Violations." -ForegroundColor Red
}
exit $LASTEXITCODE
