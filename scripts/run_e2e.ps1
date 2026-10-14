[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$StartServer,
    [switch]$ProfileLock,
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

if ($ProfileLock) {
    $delegate = Join-Path $PSScriptRoot 'run_e2e_profile.ps1'
    $delegateArgs = @{ BaseUrl = $BaseUrl }
    if ($Install) { $delegateArgs.Install = $true }
    if ($StartServer) { $delegateArgs.StartServer = $true }
    if ($CollectOnly) { $delegateArgs.CollectOnly = $true }
    if ($EnvironmentRoot) { $delegateArgs.EnvironmentRoot = $EnvironmentRoot }
    if ($Username) { $delegateArgs.Username = $Username }
    if ($Password) { $delegateArgs.Password = $Password }
    if ($ExternalDatabasePath) { $delegateArgs.ExternalDatabasePath = $ExternalDatabasePath }
    if ($LogRoot) { $delegateArgs.LogRoot = $LogRoot }
    & $delegate @delegateArgs
    exit $LASTEXITCODE
}

$python = Join-Path $root '.venv\Scripts\python.exe'
$requirements = Join-Path $root 'configuration\dependencies\requirements-e2e.txt'
$BaseUrl = $BaseUrl.TrimEnd('/')

if (-not (Test-Path $python)) { throw "Sanal ortam bulunamadı: $python" }
if (-not (Test-Path $requirements)) { throw "E2E bağımlılık dosyası bulunamadı: $requirements" }

if ($Install) {
    & $python -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) { throw 'E2E Python bağımlılıkları kurulamadı.' }
    & $python -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Playwright Chromium browser kurulamadı.' }
}

if (-not $Username -or -not $Password) {
    throw 'ECUZDAN_E2E_USERNAME ve ECUZDAN_E2E_PASSWORD process environment değişkenleri gereklidir.'
}

function Test-Health {
    try {
        $response = Invoke-WebRequest "$BaseUrl/healthz" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch { return $false }
}

$server = $null
$exitCode = 1
try {
    if (-not (Test-Health)) {
        if (-not $StartServer) { throw "Uygulama erişilebilir değil: $BaseUrl. Uygulamayı başlatın veya -StartServer kullanın." }
        if ($BaseUrl -ne 'http://127.0.0.1:5000') { throw '-StartServer yalnızca http://127.0.0.1:5000 için yapılandırılmıştır.' }
        $server = Start-Process -FilePath $python -ArgumentList @('-m','flask','--app','app:app','run','--no-debugger','--no-reload','--host','127.0.0.1','--port','5000') -WorkingDirectory $root -PassThru -WindowStyle Hidden
        $ready = $false
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            Start-Sleep -Seconds 1
            if (Test-Health) { $ready = $true; break }
        }
        if (-not $ready) { throw "Flask uygulaması healthz kontrolünde hazır olmadı. PID=$($server.Id)" }
    }
    $env:E2E_BASE_URL = $BaseUrl
    $env:ECUZDAN_E2E_USERNAME = $Username
    $env:ECUZDAN_E2E_PASSWORD = $Password
    Push-Location $root
    try {
        & $python -m pytest -q tests/e2e --base-url $BaseUrl --no-cov --tb=short -rs
        $exitCode = $LASTEXITCODE
    } finally { Pop-Location }
} finally {
    if ($server) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
exit $exitCode
