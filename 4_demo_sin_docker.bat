@echo off
cd /d "%~dp0"
set STAGEPASS_MODO=demo
echo === MODO DEMO: datos en memoria, no necesita Docker ===
echo === Abre http://localhost:8000/docs  -  NO cierres esta ventana ===
start "" cmd /c "timeout /t 4 >NUL & start http://localhost:8000/docs"
.venv\Scripts\python -m uvicorn app.main:app --port 8000 > demo_log.txt 2>&1
type demo_log.txt
echo.
echo La API se detuvo. Si hubo un error aparece arriba.
pause
