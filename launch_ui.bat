@echo off
REM Launcher for Prometheus UI
echo ========================================
echo   PROMETHEUS MODO ABSOLUTO - UI v2.1
echo ========================================
echo.
echo Iniciando interface grafica...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python prometheus_ui.py

pause
