@echo off
cd /d "%~dp0"
:: Try multiple python locations
set PY=
for %%p in (python python3 "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe") do (
    if not defined PY (%%~p --version >nul 2>&1 && set PY=%%~p)
)
if defined PY (
    "%PY%" launch.py
) else (
    echo Python not found. Please install Python 3.11+
)
pause
