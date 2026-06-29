@echo off
cd /d "%~dp0"
start "" http://localhost:8000
python -m uvicorn main:app --port 8000
pause