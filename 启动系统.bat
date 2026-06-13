@echo off
cd /d "%~dp0"

set "PYTHON="
for %%p in (
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
    "python"
    "python3"
) do (
    if not defined PYTHON (%%~p --version >nul 2>&1 && set "PYTHON=%%~p")
)
if not defined PYTHON (
    echo Python not found. Install Python 3.11+
    pause
    exit /b 1
)

echo Starting system...
"%PYTHON%" launch.py
pause
