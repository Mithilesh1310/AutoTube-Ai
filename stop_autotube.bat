@echo off
title Stop AutoTube AI Services
color 0C

echo ======================================================================
echo           Stopping AutoTube AI Services (Port 8000 & 3000)
echo ======================================================================
echo.

echo Stopping processes on Port 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping processes on Port 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] AutoTube AI services have been stopped.
echo.
pause
