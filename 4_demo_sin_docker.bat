@echo off
cd /d "%~dp0"
echo === MODO DEMO: datos en memoria, no necesita Docker ===
echo === Abre http://localhost:8000/docs  (Ctrl+C para detener) ===
set STAGEPASS_MODO=demo
start "" http://localhost:8000/docs
.venv\Scripts\python -m uvicorn app.main:app --reload
pause
