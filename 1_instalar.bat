@echo off
cd /d "%~dp0"
echo === Creando entorno virtual e instalando dependencias ===
if not exist .venv (
    py -m venv .venv || python -m venv .venv
)
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo.
echo === Listo. Ahora ejecuta 2_pruebas.bat ===
pause
