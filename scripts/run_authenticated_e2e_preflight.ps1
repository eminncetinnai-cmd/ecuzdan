[CmdletBinding()]
param(
    [string]$EnvironmentRoot = $env:E2E_PROFILE_ENV_ROOT,
    [string]$ExternalDatabasePath = $env:E2E_EXTERNAL_DB_PATH,
    [string]$BaseUrl = $(if ($env:E2E_BASE_URL) { $env:E2E_BASE_URL } else { 'http://127.0.0.1:5000' }),
    [int]$Port = 5000
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
if (-not $EnvironmentRoot) { $EnvironmentRoot = Join-Path $env:TEMP 'e-cuzdan-e2e-profile-venv' }
$environmentFull = [System.IO.Path]::GetFullPath($EnvironmentRoot)
$projectVenv = [System.IO.Path]::GetFullPath((Join-Path $root '.venv'))
$activeDb = [System.IO.Path]::GetFullPath((Join-Path $root 'e_cuzdan_v15.db'))
$lock = Join-Path $root 'configuration\dependencies\requirements-e2e-lock.txt'
if ($environmentFull.Equals($projectVenv, [System.StringComparison]::OrdinalIgnoreCase) -or $environmentFull.StartsWith($projectVenv + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Preflight active .venv hedefini reddetti.' }
if (-not $ExternalDatabasePath) { throw 'ExternalDatabasePath zorunludur; active DB’ye fallback yoktur.' }
$externalDb = [System.IO.Path]::GetFullPath($ExternalDatabasePath)
if (-not (Test-Path -LiteralPath $externalDb)) { throw "External DB clone bulunamadı: $externalDb" }
if ($externalDb.Equals($activeDb, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Preflight active DB path’i reddetti.' }
$python = if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) { Join-Path $environmentFull 'Scripts\python.exe' } else { Join-Path $environmentFull 'bin/python' }
$lockItem = Get-Item -LiteralPath $lock -ErrorAction Stop
$dbItem = Get-Item -LiteralPath $externalDb -ErrorAction Stop
$listenerRows = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | ForEach-Object { $p=Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; [ordered]@{pid=$_.OwningProcess;process_name=if($p){$p.ProcessName}else{$null};process_path=if($p){$p.Path}else{$null}} })
$credUsernamePresent = [bool]($env:ECUZDAN_E2E_USERNAME)
$credPasswordPresent = [bool]($env:ECUZDAN_E2E_PASSWORD)
$healthStatus = 'UNAVAILABLE'
try { $healthStatus = (Invoke-WebRequest ($BaseUrl.TrimEnd('/') + '/healthz') -UseBasicParsing -TimeoutSec 5).StatusCode } catch {}
$env:DATABASE_URL = 'sqlite:///' + $externalDb.Replace('\','/')
$env:FLASK_ENV = 'testing'
$env:TESTING = 'true'
$env:DISABLE_BACKGROUND_SERVICE = 'true'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = $root
$preflight = [ordered]@{
    timestamp=(Get-Date).ToString('o')
    base_url=$BaseUrl
    production_url_detected=$BaseUrl -match '(^|\.)prod(uction)?(\.|/|:)' 
    environment_root=$environmentFull
    active_venv_path=$projectVenv
    external_venv=$environmentFull -ne $projectVenv
    python_exists=Test-Path -LiteralPath $python
    e2e_lock=[ordered]@{path=$lock;bytes=[int64]$lockItem.Length;sha256=(Get-FileHash -LiteralPath $lock -Algorithm SHA256).Hash}
    external_db=[ordered]@{path=$externalDb;bytes=[int64]$dbItem.Length;sha256=(Get-FileHash -LiteralPath $externalDb -Algorithm SHA256).Hash;active_db_path_match=$externalDb.Equals($activeDb,[System.StringComparison]::OrdinalIgnoreCase)}
    healthz_status=$healthStatus
    listener_count=$listenerRows.Count
    listeners=$listenerRows
    credential_presence=[ordered]@{username_present=$credUsernamePresent;password_present=$credPasswordPresent;values_read=$false;values_logged=$false}
    background_service_disabled=($env:DISABLE_BACKGROUND_SERVICE -eq 'true')
    active_venv_mutated=$false
    active_db_mutated=$false
    financial_rows_read=$false
    status=if($healthStatus -eq 200 -and $listenerRows.Count -le 1 -and $credUsernamePresent -and $credPasswordPresent -and (Test-Path -LiteralPath $python) -and ($externalDb -ne $activeDb)){'READY_FOR_AUTHENTICATED_E2E'}else{'REVIEW'}
    policy='Credential-safe preflight only; no login submit, process stop, active venv change, active DB/WAL/SHM mutation or financial row read.'
}
$out=Join-Path $root 'reports\authenticated_e2e_preflight_20260826.json'
$preflight|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $out -Encoding UTF8
$preflight|ConvertTo-Json -Depth 8
