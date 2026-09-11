@echo off
title AutoTube AI - Autonomous Multi-Channel Studio
color 0B

echo ======================================================================
echo           AutoTube AI -- Autonomous Hindi Kids Content SaaS
echo ======================================================================
echo.

:: 1. Verify Prerequisites
echo [1/4] Checking environment prerequisites...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not found in PATH!
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
echo       - Python: OK
echo       - Node/npm: OK

:: 2. Ensure Storage Directories
echo [2/4] Initializing local storage directories...
if not exist "storage" mkdir storage
if not exist "storage\renders" mkdir storage\renders
if not exist "storage\audio" mkdir storage\audio
if not exist "storage\thumbnails" mkdir storage\thumbnails
echo       - Storage: OK

:: 3. Start Backend Server
echo [3/4] Launching AutoTube Backend on http://127.0.0.1:8000...
start "AutoTube AI Backend (FastAPI :8000)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: 4. Start Frontend Server
echo [4/4] Launching AutoTube Frontend on http://localhost:3000...
start "AutoTube AI Frontend (Next.js :3000)" cmd /k "cd frontend && npm run dev"

:: Wait for servers to spin up and launch browser
echo.
echo Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo Opening AutoTube AI Dashboard in your browser...
start http://localhost:3000

echo.
echo ======================================================================
echo   AutoTube AI is running!
echo   - Web Dashboard: http://localhost:3000
echo   - Backend API:   http://127.0.0.1:8000
echo   - API Docs:      http://127.0.0.1:8000/docs
echo.
echo   To stop all services, run: stop_autotube.bat
echo ======================================================================
echo.
pause
