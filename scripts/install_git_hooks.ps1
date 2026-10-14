# E-Cüzdan Git Hooks Kurulum Scripti (PowerShell)
$Hooks = @("pre-commit", "pre-push")
$HooksDir = Join-Path $PSScriptRoot "hooks"
$GitHooksDir = Join-Path $PSScriptRoot "..\.git\hooks"

if (-not (Test-Path $GitHooksDir)) {
    Write-Error "HATA: .git\hooks dizini bulunamadı ($GitHooksDir). Proje git reposu mu?"
    exit 1
}

foreach ($Hook in $Hooks) {
    $HookSource = Join-Path $HooksDir $Hook
    $HookDest = Join-Path $GitHooksDir $Hook

    if (Test-Path $HookSource) {
        Copy-Item $HookSource -Destination $HookDest -Force
        Write-Host "✅ E-Cüzdan Git $Hook hook'u başarıyla kuruldu: $HookDest" -ForegroundColor Green
    } else {
        Write-Warning "UYARI: Hook kaynak dosyası bulunamadı: $HookSource"
    }
}

Write-Host "`nGit kancaları hazır:" -ForegroundColor Cyan
Write-Host "  - pre-commit: Tasarım sistemi, Mimari kapısı, Mypy ve Ledger Watchdog" -ForegroundColor Gray
Write-Host "  - pre-push:   verify_all.py (Query profiler, IDOR fuzzer, testler ve kapsama)" -ForegroundColor Gray
