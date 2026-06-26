@echo off
cd /d C:\Users\cvazquez\AppData\Roaming\RStudio\DCode_

taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM python3.exe /T >nul 2>&1
timeout /t 1 >nul

powershell -WindowStyle Hidden -Command ^
"Start-Process python3 -ArgumentList '-m uvicorn awgi:app --host 0.0.0.0 --port 1357 --reload' -WindowStyle Hidden"

timeout /t 2 >nul
start "" powershell -WindowStyle Hidden -Command "ngrok http 1357"
exit
