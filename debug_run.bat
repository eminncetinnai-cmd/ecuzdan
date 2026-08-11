@echo off
title E-Cuzdan Hata Ayiklama Modu
echo ===================================================
echo    E-CUZDAN TEKNIK HATA TESPIT MODU
echo ===================================================
echo.
echo Python surumu:
python --version
echo.
echo Kutuphaneler kontrol ediliyor...
python -c "import flask; import flask_sqlalchemy; import dotenv; print('Temel kutuphaneler TAMAM')"
if %errorlevel% neq 0 (
    echo [!] HATA: Kutuphaneler eksik!requirements.txt yukleniyor...
    python -m pip install -r requirements.txt
)
echo.
echo Sunucu baslatiliyor (Lutfen cikan hatalari kopyalayip Manus'a iletin)...
echo.
python app.py
echo.
echo ===================================================
echo Sunucu durdu veya hata verdi. 
pause
