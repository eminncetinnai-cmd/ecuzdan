<#
.SYNOPSIS
    E-Cüzdan Otomatik Veritabanı Bakım ve Sağlık Görevi
.DESCRIPTION
    SQLite veritabanı üzerinde bütünlük kontrolü (integrity_check), anlık snapshot
    yedeği alma, WAL checkpoint, defragmentasyon (VACUUM) ve sorgu optimizasyonu
    (PRAGMA optimize) boru hattını çalıştırır. Windows Task Scheduler veya manuel
    bakım için uygundur.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/run_maintenance.ps1
#>

[CmdletBinding()]
param (
    [switch]$NoSnapshot,
    [switch]$StatusOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  E-CÜZDAN VERİTABANI BAKIM OTOMASYONU" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$pythonCmd = "python"
if (-not (Get-Command $pythonCmd -ErrorAction SilentlyContinue)) {
    Write-Error "Python yürütülebilir dosyası bulunamadı. Lütfen PATH ayarlarını kontrol edin."
    exit 1
}

$argsList = @("scripts/maintenance.py")
if ($StatusOnly) {
    $argsList += "--status"
} else {
    $argsList += "--execute"
    if ($NoSnapshot) {
        $argsList += "--no-snapshot"
    }
}

& $pythonCmd $argsList
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    if (-not $StatusOnly) {
        Write-Host "`n[TEMİZLİK] Disk ve önbellek temizliği yürütülüyor..." -ForegroundColor Cyan
        & $pythonCmd "scripts/clean_caches.py"
    }
    Write-Host "`n[BAŞARILI] Veritabanı ve disk bakımı başarıyla tamamlandı." -ForegroundColor Green
} else {
    Write-Host "`n[HATA] Veritabanı bakımı sırasında hata oluştu (Exit Code: $exitCode)." -ForegroundColor Red
}

exit $exitCode
