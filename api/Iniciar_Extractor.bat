@echo off
title Iniciar SCT Extractor
echo ===================================================
echo Iniciando el Servidor de SCT Extractor...
echo ===================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en la carpeta venv.
    pause
    exit
)

echo Iniciando entorno virtual y servidor...
start "Servidor SCT" cmd /c ".\venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo.
echo Esperando a que el servidor arranque...
timeout /t 3 /nobreak > NUL

echo Abriendo la aplicacion en el navegador...
start http://localhost:8000

echo.
echo ===================================================
echo [LISTO] Puedes minimizar esta ventana negra.
echo Para apagar el sistema, cierra la otra ventana que dice "Servidor SCT".
echo ===================================================
pause
