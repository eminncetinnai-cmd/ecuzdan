@echo off
setlocal
title E-Cuzdan Akilli Baslatici v15

REM Çalışma dizinini bu dosyanın olduğu klasöre ayarla
cd /d "%~dp0"

echo ===================================================
echo        E-CUZDAN YONETIM SISTEMI HAZIRLANIYOR
echo ===================================================
echo.
echo Calisma dizini: %CD%
echo.

REM Python kontrol et
echo [1/6] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] HATA: Python yuklu degil!
    echo Lutfen once Python 3.7+ yukleyin ve tekrar deneyin.
    echo Python'u https://www.python.org/downloads/ adresinden indirebilirsiniz.
    pause
    exit /b 1
)
python --version
echo [+] Python bulundu

REM requirements.txt kontrol et
echo [2/6] requirements.txt kontrol ediliyor...
if not exist "requirements.txt" (
    echo [!] HATA: requirements.txt dosyasi bulunamadi!
    echo Lutfen dosyanin bu klasorde oldugundan emin olun.
    pause
    exit /b 1
)
echo [+] requirements.txt bulundu

REM Kutuphaneleri yukle
echo [3/6] Kutuphaneler kontrol ediliyor ve yukleniyor...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] UYARI: Bazı kutuphaneler yuklenemedi.
    echo Program yine de calisabilir ancak hatalar olabilir.
) else (
    echo [+] Kutuphaneler basariyla yuklendi
)

REM Ek finansal analiz kutuphanelerini yukle
echo [4/6] Ek finansal analiz kutuphaneleri yukleniyor...
python -m pip install yfinance scipy pandas numpy
if %errorlevel% neq 0 (
    echo [!] UYARI: Bazı finansal analiz kutuphaneleri yuklenemedi.
    echo Strateji Motoru ozelligi calismayabilir.
) else (
    echo [+] Finansal analiz kutuphaneleri basariyla yuklendi
)

REM app.py kontrol et
echo [5/6] app.py kontrol ediliyor...
if not exist "app.py" (
    echo [!] HATA: app.py dosyasi bulunamadi!
    echo Lutfen dosyanin bu klasorde oldugundan emin olun.
    pause
    exit /b 1
)
echo [+] app.py bulundu

REM Sunucuyu baslat
echo [6/6] Sunucu baslatiliyor...
echo.
echo NOT: Sunucu penceresi acik kalacaktir. Kapattiginizda program durur.
echo.
start "E-CUZDAN SUNUCUSU" cmd /k "cd /d "%~dp0" && python app.py"

REM Sunucunun hazir olmasini bekle
echo Sunucu baslatiliyor, bekleniyor...
set "count=0"
:loop
set /a "count+=1"
netstat -ano | find "5000" | find "LISTENING" >nul
if %errorlevel% equ 0 (
    echo.
    echo [+] Sistem Hazir!
    echo Tarayici otomatik olarak aciliyor...
    echo.
    echo ===================================================
    echo    E-CUZDAN AKTIF (PORT: 5000)
    echo ===================================================
    echo.
    echo Uygulama tarayicinizda aciliyor.
    echo Eger acilmadiysa manuel olarak: http://localhost:5000

    echo.
    echo Bu pencereyi simge durumuna kucultebilirsiniz.
    timeout /t 3
    start http://localhost:5000
    exit
)
if %count% gtr 30 (
    echo.
    echo [!] HATA: Sunucu baslatilamadi (Zaman asimi).
    echo Lutfen asagidaki adimlari kontrol edin:
    echo 1. Python yuklu mu?
    echo 2. Tum kutuphaneler yuklendi mi?
    echo 3. app.py dosyasi var mi?
    echo 4. Port 5000 baska bir uygulama tarafindan kullaniliyor mi?
    echo.
    echo Log dosyalarini kontrol etmek icin logs klasorune bakin.
    pause
    exit /b 1
)
<nul set /p "=. "
timeout /t 1 >nul
goto loop
