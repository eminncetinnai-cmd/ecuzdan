@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

title E-Cuzdan -- Intelligent Wealth Platform

echo(
echo   ============================================================
echo     _____         ____ _   _ _____ ____    _    _   _ 
echo    ^| ____^|       / ___^| ^| ^| ^|__  /^|  _ \  / \  ^| \ ^| ^|
echo    ^|  _^|  _____ ^| ^|   ^| ^| ^| ^| / / ^| ^| ^| ^|/ _ \ ^|  ^\ ^| ^|
echo    ^| ^|___^|_____^|^| ^|___^| ^|_^| ^|/ /_ ^| ^|_^| / ___ \^| ^|^\  ^|
echo    ^|_____^|       ^\____^|^\___//____^|^|____/_/   ^\_\_^| ^\_^|
echo(
echo     E-CUZDAN -- AKILLI VARLIK VE FINANS YONETIM PLATFORMU
echo   ============================================================
echo(

:: 1. Prefer existing .venv Python if available
if not exist ".venv\Scripts\python.exe" goto :try_py
".venv\Scripts\python.exe" scripts\runtime\bootstrap.py %*
if not errorlevel 1 goto :end
echo [.venv Python basarisiz oldu, sistem Python deneniyor...]

:try_py
:: 2. Search for Windows py launcher
where py >nul 2>nul
if errorlevel 1 goto :try_python
py -3.13 scripts\runtime\bootstrap.py %* 2>nul
if not errorlevel 1 goto :end
py scripts\runtime\bootstrap.py %*
if not errorlevel 1 goto :end

:try_python
:: 3. Search for python in PATH
where python >nul 2>nul
if errorlevel 1 goto :no_python
python scripts\runtime\bootstrap.py %*
goto :end

:no_python
echo(
echo ============================================================
echo   E-CUZDAN RUNTIME HATASI: PYTHON BULUNAMADI
echo ============================================================
echo   Sistemde Python calistiricisi tespit edilemedi.
echo   Lutfen https://www.python.org/downloads/ adresinden
echo   Python 3.13 kurun ve "Add Python to PATH" secenegini isaretleyin.
echo ============================================================
echo(
pause
exit /b 1

:end
if not errorlevel 1 goto :success
echo(
echo ============================================================
echo   E-Cuzdan calismasi bir hata ile sonlandi.
echo ============================================================
echo(
pause
exit /b 1

:success
if "%~1"=="--check-only" goto :eof
echo(
echo E-Cuzdan sunucusu durduruldu.
echo Pencereyi kapatmak icin bir tusa basin...
pause >nul
goto :eof
