@echo off
chcp 936 >nul
setlocal enabledelayedexpansion

title Military Rural System v1.3.0

echo.
echo ========================================
echo   Military Rural System v1.3.0
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "backend\data" mkdir "backend\data" >nul 2>&1
if not exist "backend\logs" mkdir "backend\logs" >nul 2>&1

echo [1/4] Checking port...
echo.

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   Port 8000 in use, cleaning...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   [OK] Port cleared
) else (
    echo   [OK] Port 8000 free
)

netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   Port 5173 in use, cleaning...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   [OK] Port cleared
) else (
    echo   [OK] Port 5173 free
)

echo.

echo [2/4] Detect startup mode...

set "PORTABLE_EXE="
if exist "dist\electron\win-unpacked\military-rural-system.exe" (
    set "PORTABLE_EXE=dist\electron\win-unpacked\military-rural-system.exe"
    echo   [OK] Portable version detected
    goto START_PORTABLE
)

set "START_MODE="
if exist "dist\backend\windows\military-rural-backend.exe" (
    set "START_MODE=packaged"
    set "BACKEND_CMD=dist\backend\windows\military-rural-backend.exe"
    set "BACKEND_CWD=%CD%"
    echo   [OK] Packaged version detected
    goto START_BACKEND
)

if exist "backend\.venv\Scripts\python.exe" (
    set "START_MODE=venv"
    set "BACKEND_CMD=backend\.venv\Scripts\python.exe"
    set "BACKEND_CWD=%CD%\backend"
    echo   [OK] Python venv detected
    goto START_BACKEND
)

if exist "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe" (
    set "START_MODE=python64"
    set "BACKEND_CMD=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
    set "BACKEND_CWD=%CD%\backend"
    echo   [OK] Python 3.11 64-bit detected
    goto START_BACKEND
)
echo.

python --version >nul 2>&1
if not errorlevel 1 (
    set "START_MODE=python"
    set "BACKEND_CMD=python"
    set "BACKEND_CWD=%CD%\backend"
    echo   [OK] System Python detected
    goto START_BACKEND
)

echo.
echo   [ERROR] No Python runtime found!
echo   Please install Python 3.11+ first.
echo.
pause
exit /b 1

:START_PORTABLE
echo.
echo [3/4] Starting portable app...
start "" "%PORTABLE_EXE%"
echo   [OK] Portable app started
goto STARTUP_DONE

:START_BACKEND
echo.
echo [3/4] Starting backend...

set "FRONTEND_DIST_PATH=%CD%\resources\frontend"

if "%START_MODE%"=="packaged" (
    start "Backend" /B "%BACKEND_CMD%"
    echo   [OK] Packaged backend started
) else (
    start "Backend" /B "%BACKEND_CMD%" backend\start.py
    echo   [OK] Python backend started
)

echo   Waiting for backend...
set "BACKEND_READY=0"
for /L %%i in (1,1,60) do (
    powershell -Command "try { $r=Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 2 -UseBasicParsing; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_READY=1"
        echo   [OK] Backend ready (%%i sec)
        goto BACKEND_DONE
    )
    timeout /t 1 /nobreak >nul
)

:BACKEND_DONE
if "%BACKEND_READY%"=="0" (
    echo   [WARN] Backend startup timeout
    echo   Check http://localhost:8000 manually
) else (
    echo   [OK] Backend service ready
)

echo.
echo [4/4] Opening browser...
start http://localhost:8000
echo   [OK] Browser opened

:STARTUP_DONE
echo.
echo ========================================
echo   System started successfully!
echo ========================================
echo.
echo   URL: http://localhost:8000
echo   Default account: admin
echo   Password: check backend startup log
echo.
echo   Close this window to stop backend service.
echo.

if not "%PORTABLE_EXE%"=="" goto :EOF

echo   Backend running. Press Ctrl+C or close window to stop.
echo.

:WATCHDOG
if "%START_MODE%"=="packaged" (
    tasklist | findstr "military-rural-backend.exe" >nul 2>&1
) else (
    tasklist | findstr "python.exe" >nul 2>&1
)
if errorlevel 1 (
    echo.
    echo   [WARN] Backend process exited, restarting in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto START_BACKEND
)

timeout /t 10 /nobreak >nul
goto WATCHDOG

endlocal
