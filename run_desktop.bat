@echo off
echo [*] Iniciando Prometheus Supreme - Interface Desktop
echo.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python prometheus_gui.py
pause
