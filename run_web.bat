@echo off
echo [*] Iniciando Prometheus Supreme - Interface Web
echo [*] Acesse em: http://localhost:8100
echo.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python prometheus_web.py
pause
