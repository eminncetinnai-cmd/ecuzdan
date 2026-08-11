@echo off
setlocal
cd /d "%~dp0"

echo E-Cuzdan başlatılıyor...

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    goto :run
)

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
    goto :run
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :run
)

echo Python bulunamadı. Lütfen Python kurulu olduğundan emin olun.
pause
exit /b 1

:run
if defined PYTHON_ARGS (
    "%PYTHON_EXE%" %PYTHON_ARGS% app.py
) else (
    "%PYTHON_EXE%" app.py
)

if errorlevel 1 (
    echo Başlatma başarısız oldu.
    pause
)
