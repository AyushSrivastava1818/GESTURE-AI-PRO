@echo off
title GestureAI Pro Launcher
echo =============================================
echo   GestureAI Pro - Intelligent Whiteboard
echo =============================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo [INFO] Setting up virtual environment, please wait...
    python -m venv venv
    echo [INFO] Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
    echo.
)

echo [INFO] Activating virtual environment...
echo [INFO] Launching whiteboard... 
echo [INFO] Make sure your webcam is connected!
echo.
echo Press ESC inside the whiteboard window to quit.
echo =============================================
echo.

:: Run the app using the venv Python
venv\Scripts\python.exe main.py

echo.
echo [INFO] Application closed. Press any key to exit.
pause >nul
