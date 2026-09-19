@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 (
        echo No se pudo crear el entorno virtual. Instalá Python 3.11 o superior.
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m src.main --run-all
if errorlevel 1 exit /b 1

if not exist "results\map.html" (
    echo La corrida terminó sin generar results\map.html.
    exit /b 1
)
start "" "%CD%\results\map.html"
