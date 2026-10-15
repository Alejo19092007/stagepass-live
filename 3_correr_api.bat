@echo off
cd /d "%~dp0"
echo === Levantando MySQL y MongoDB (requiere Docker Desktop abierto) ===
docker compose up -d
echo.
echo === API en http://localhost:8000/docs  (Ctrl+C para detener) ===
start "" http://localhost:8000/docs
.venv\Scripts\python -m uvicorn app.main:app --reload
pause
