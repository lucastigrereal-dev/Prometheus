@echo off
REM PROMETHEUS V2 LAUNCHER
REM Quick launcher for Prometheus Integrated System

echo.
echo ========================================================================
echo PROMETHEUS INTEGRATED SYSTEM - V1 + V2
echo ========================================================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Menu
echo Select option:
echo.
echo [1] Start Prometheus Integrated (main_integrated.py)
echo [2] Test Integration Bridge (integration_bridge.py)
echo [3] Validate System (validate_integration.py)
echo [4] Analyze Integration (analyze_integration.py)
echo [5] Exit
echo.

set /p choice="Enter option (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting Prometheus Integrated System...
    echo.
    .venv\Scripts\python.exe main_integrated.py
) else if "%choice%"=="2" (
    echo.
    echo Testing Integration Bridge...
    echo.
    .venv\Scripts\python.exe integration_bridge.py
    pause
) else if "%choice%"=="3" (
    echo.
    echo Validating System...
    echo.
    .venv\Scripts\python.exe validate_integration.py
    pause
) else if "%choice%"=="4" (
    echo.
    echo Analyzing Integration...
    echo.
    .venv\Scripts\python.exe analyze_integration.py
    pause
) else if "%choice%"=="5" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid option!
    pause
    exit /b 1
)
