@echo off
echo ==========================================
echo   Smart Attendance System - Quick Start
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python and try again.
    pause
    exit /b
)

:: Navigate to the specific project directory where the code is
cd /d "%~dp0"
cd "Smart Attendance System\FACE ATTENDANCE"

echo [STEP 1/1] Starting the Attendance System...
echo.
echo The app will be available at: http://127.0.0.1:7860
echo.

:: Run the script
python face_attendance.py

pause
