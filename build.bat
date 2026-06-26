@echo off
cd /d C:\Users\cvazquez\AppData\Roaming\RStudio\DCode_

echo [1/3] Ofuscando Python con PyArmor...
pyarmor gen -O dist awgi.py testte.py crypto.py seed.py
if errorlevel 1 (
    echo ERROR: PyArmor falló.
    pause
    exit /b 1
)

echo [2/3] Copiando ficheros estaticos...
copy /Y template.html dist\template.html >nul
if not exist dist\dat mkdir dist\dat
xcopy /E /Y /Q dat\* dist\dat\ >nul

echo [3/3] Listo. dist\ contiene el build ofuscado.
echo   - Arranca con run_services.bat
pause
