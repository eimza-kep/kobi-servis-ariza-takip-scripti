@echo off
chcp 65001 >nul
echo =================================================================
echo        KOBİ TEKNİK SERVİS VE ARIZA TAKİP SİSTEMİ BAŞLATICI
echo =================================================================
echo.
echo Sunucu hazırlanıyor ve başlatılıyor...
echo Port: 8087
echo.
start "" http://localhost:8087
python server.py
pause
