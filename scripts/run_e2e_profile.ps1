[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$StartServer,
    [switch]$CollectOnly,
    [string]$EnvironmentRoot = $env:E2E_PROFILE_ENV_ROOT,
    [string]$BaseUrl = $(if ($env:E2E_BASE_URL) { $env:E2E_BASE_URL } else { 'http://127.0.0.1:5000' }),
    [string]$Username = $env:ECUZDAN_E2E_USERNAME,
    [string]$Password = $env:ECUZDAN_E2E_PASSWORD,
    [string]$ExternalDatabasePath = $env:E2E_EXTERNAL_DB_PATH,
    [string]$LogRoot = $env:E2E_LOG_DIR
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $EnvironmentRoot) { $EnvironmentRoot = Join-Path $env:TEMP 'e-cuzdan-e2e-profile-venv' }
$lock = Join-Path $root 'configuration\dependencies\requirements-e2e-lock.txt'
$projectVenv = [System.IO.Path]::GetFullPath((Join-Path $root '.venv'))
$environmentFull = [System.IO.Path]::GetFullPath($EnvironmentRoot)

if ($environmentFull -eq $projectVenv -or $environmentFull.StartsWith($projectVenv + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'E2E profile runner active .venv üzerinde işlem yapamaz; E2E_PROFILE_ENV_ROOT dış bir venv olmalıdır.'
}
if (-not (Test-Path -LiteralPath $lock)) { throw "E2E lock dosyası bulunamadı: $lock" }

$activeDb = [System.IO.Path]::GetFullPath((Join-Path $root 'e_cuzdan_v15.db'))
if ($ExternalDatabasePath) {
    $externalDb = [System.IO.Path]::GetFullPath($ExternalDatabasePath)
    if (-not (Test-Path -LiteralPath $externalDb)) { throw "External E2E DB clone bulunamadı: $externalDb" }
    if ($externalDb.Equals($activeDb, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'E2E runner active finansal DB’yi hedefleyemez; external clone gereklidir.' }
    $env:DATABASE_URL = 'sqlite:///' + $externalDb.Replace('\\','/')
}
if ($StartServer -and -not $ExternalDatabasePath) {
    throw 'E2E -StartServer için -ExternalDatabasePath veya E2E_EXTERNAL_DB_PATH zorunludur; active DB’ye bağlanma reddedildi.'
}
if ($StartServer) {
    $env:FLASK_ENV = 'testing'
    $env:TESTING = 'true'
    $env:DISABLE_BACKGROUND_SERVICE = 'true'
    if (-not $LogRoot) { $LogRoot = Join-Path $env:TEMP 'e-cuzdan-e2e-profile-logs' }
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    $env:ECUZDAN_LOG_DIR = [System.IO.Path]::GetFullPath($LogRoot)
}

$python = Join-Path $environmentFull 'Scripts\\python.exe'
$isWindows = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)
if (-not $isWindows) { $python = Join-Path $environmentFull 'bin/python' }
if (-not (Test-Path -LiteralPath $python)) {
    $systemPython = (Get-Command python -ErrorAction Stop).Path
    New-Item -ItemType Directory -Path $environmentFull -Force | Out-Null
    & $systemPython -m venv --copies $environmentFull
    if ($LASTEXITCODE -ne 0) { throw 'E2E profile virtual environment oluşturulamadı.' }
}

if ($Install) {
    & $python -m pip install --disable-pip-version-check --no-input --no-cache-dir --require-hashes -r $lock
    if ($LASTEXITCODE -ne 0) { throw 'E2E profile hash-lock kurulumu başarısız.' }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'E2E profile pip check başarısız.' }
    & $python -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Playwright Chromium kurulamadı.' }
}

if (-not $CollectOnly -and (-not $Username -or -not $Password)) {
    throw 'Authenticated E2E için ECUZDAN_E2E_USERNAME ve ECUZDAN_E2E_PASSWORD process environment değişkenleri gereklidir.'
}
if (-not $CollectOnly -and $ExternalDatabasePath -and -not $StartServer) {
    throw 'External DB authenticated acceptance için -StartServer zorunludur; mevcut server’ın DB path’i doğrulanmadan test çalıştırılmaz.'
}

$BaseUrl = $BaseUrl.TrimEnd('/')
$baseUri = [Uri]$BaseUrl
if ($StartServer -and ($baseUri.Host -notin @('127.0.0.1','localhost'))) { throw '-StartServer yalnız loopback BaseUrl ile kullanılabilir.' }
if ($StartServer -and $ExternalDatabasePath -and $baseUri.Port -eq 5000) { throw 'External DB E2E için active staging portu 5000 kullanılamaz; isolated BaseUrl/port (ör. 5010) verin.' }
$env:E2E_BASE_URL = $BaseUrl
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = $root
$server = $null
$exitCode = 1
try {
    function Test-Health {
        try {
            $response = Invoke-WebRequest "$BaseUrl/healthz" -UseBasicParsing -TimeoutSec 2
            return $response.StatusCode -eq 200
        } catch { return $false }
    }

    if ($CollectOnly) {
        Push-Location $root
        try {
            & $python -m pytest -q tests/e2e --collect-only -p no:cacheprovider -p no:cov -o addopts= --disable-warnings
            $exitCode = $LASTEXITCODE
        } finally { Pop-Location }
    } else {
            if (-not (Test-Health)) {
        if (-not $StartServer) { throw "Uygulama erişilebilir değil: $BaseUrl. Uygulamayı başlatın veya -StartServer kullanın." }
        if ($baseUri.Port -lt 1024 -or $baseUri.Port -gt 65535) { throw "ServerPort geçersiz: $($baseUri.Port)" }
        if (@(Get-NetTCPConnection -State Listen -LocalPort $baseUri.Port -ErrorAction SilentlyContinue).Count -ne 0) { throw "StartServer portu zaten kullanımda: $($baseUri.Port)" }
        $server = Start-Process -FilePath $python -ArgumentList @('-m','flask','--app','app:app','run','--no-debugger','--no-reload','--host','127.0.0.1','--port',([string]$baseUri.Port)) -WorkingDirectory $root -PassThru -WindowStyle Hidden

            $ready = $false
            for ($attempt = 0; $attempt -lt 60; $attempt++) {
                Start-Sleep -Seconds 1
                if (Test-Health) { $ready = $true; break }
            }
            if (-not $ready) { throw "Flask uygulaması healthz kontrolünde hazır olmadı. PID=$($server.Id)" }
        }
        $env:ECUZDAN_E2E_USERNAME = $Username
        $env:ECUZDAN_E2E_PASSWORD = $Password
        Push-Location $root
        try {
            & $python -m pytest -q tests/e2e --base-url $BaseUrl --no-cov --tb=short -rs
            $exitCode = $LASTEXITCODE
        } finally { Pop-Location }
    }
} finally {
    if ($server) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (@(Get-NetTCPConnection -State Listen -LocalPort $baseUri.Port -ErrorAction SilentlyContinue).Count -ne 0) { Write-Warning "Runner’ın başlattığı PID sonrası listener kapanmadı: $($baseUri.Port)" }
    }
}
exit $exitCode
