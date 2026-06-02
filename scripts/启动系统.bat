@echo off
setlocal enabledelayedexpansion

title 军队乡村振兴管理系统 v1.1.0

echo.
echo ========================================
echo   军队乡村振兴管理系统 v1.1.0
echo ========================================
echo.

:: 切换到项目根目录（bat文件所在目录的上一级）
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

:: 确保必要目录存在
if not exist "backend\data" mkdir "backend\data" >nul 2>&1
if not exist "backend\logs" mkdir "backend\logs" >nul 2>&1

:: ======== 第1步：清理端口 ========
echo [1/4] 检查端口占用...
echo.

:: 清理8000端口
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo   端口 8000 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   [OK] 端口已清理
) else (
    echo   [OK] 端口 8000 空闲
)

:: 清理5173端口
netstat -ano | findstr :5173 | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo   端口 5173 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   [OK] 端口已清理
) else (
    echo   [OK] 端口 5173 空闲
)

echo.

:: ======== 第2步：检测启动模式 ========
echo [2/4] 检测运行模式...

:: 优先检测便携版 Electron 应用（便携版自带后端）
set "PORTABLE_EXE="
if exist "dist\electron\win-unpacked\军队乡村振兴管理系统.exe" (
    set "PORTABLE_EXE=dist\electron\win-unpacked\军队乡村振兴管理系统.exe"
    echo   [OK] 检测到便携版应用 (dist\electron\win-unpacked)
    goto :START_PORTABLE
)
if exist "dist\win-unpacked\军队乡村振兴管理系统.exe" (
    set "PORTABLE_EXE=dist\win-unpacked\军队乡村振兴管理系统.exe"
    echo   [OK] 检测到便携版应用 (dist\win-unpacked)
    goto :START_PORTABLE
)

:: 检测打包后的后端 exe
if exist "dist\backend\windows\military-rural-backend.exe" (
    set "START_MODE=packaged"
    set "BACKEND_CMD=dist\backend\windows\military-rural-backend.exe"
    set "BACKEND_CWD=%CD%"
    echo   [OK] 检测到打包后端 (dist\backend\windows)
    goto :START_BACKEND
)

if exist "resources\backend\military-rural-backend.exe" (
    set "START_MODE=packaged"
    set "BACKEND_CMD=resources\backend\military-rural-backend.exe"
    set "BACKEND_CWD=%CD%"
    echo   [OK] 检测到打包后端 (resources)
    goto :START_BACKEND
)

:: 检测虚拟环境
if exist "backend\.venv\Scripts\python.exe" (
    set "START_MODE=venv"
    set "BACKEND_CMD=backend\.venv\Scripts\python.exe"
    set "BACKEND_CWD=%CD%\backend"
    echo   [OK] 检测到 Python 虚拟环境
    goto :START_BACKEND
)

:: 检测系统 Python
python --version >nul 2>&1
if not errorlevel 1 (
    set "START_MODE=python"
    set "BACKEND_CMD=python"
    set "BACKEND_CWD=%CD%\backend"
    echo   [OK] 使用系统 Python
    goto :START_BACKEND
)

echo.
echo   [错误] 未找到 Python 运行环境！
echo   请确保已安装 Python 3.11+ 或已构建后端包。
echo.
pause
exit /b 1

:: ======== 启动便携版 ========
:START_PORTABLE
echo.
echo [3/4] 启动便携版应用...
start "" "%PORTABLE_EXE%"
echo   [OK] 便携版应用已启动
goto :STARTUP_DONE

:: ======== 第3步：启动后端 ========
:START_BACKEND
echo.
echo [3/4] 启动后端服务...

:: 设置环境变量（确保前端静态文件可被找到）
set "FRONTEND_DIST_PATH=%CD%\frontend\dist"

if "%START_MODE%"=="packaged" (
    start "军队乡村振兴管理系统-后端" /B "%BACKEND_CMD%"
    echo   [OK] 打包后端已启动
) else (
    cd /d "%BACKEND_CWD%"
    if "%START_MODE%"=="venv" (
        start "军队乡村振兴管理系统-后端" /B "%BACKEND_CMD%" start.py
    ) else (
        start "军队乡村振兴管理系统-后端" /B "%BACKEND_CMD%" start.py
    )
    echo   [OK] Python 后端已启动
    cd /d "%PROJECT_DIR%"
)

:: 等待后端就绪
echo   等待后端初始化...
set "BACKEND_READY=0"
for /L %%i in (1,1,60) do (
    curl -s -o nul -w "%%{http_code}" http://localhost:8000/health 2>nul | findstr "200" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_READY=1"
        echo   [OK] 后端已就绪 ^(耗时 %%i 秒^)
        goto :BACKEND_DONE
    )
    timeout /t 1 /nobreak >nul
)

:BACKEND_DONE
if "%BACKEND_READY%"=="0" (
    echo   [警告] 后端启动超时，但服务可能仍在初始化中...
    echo   请稍后访问 http://localhost:8000
) else (
    echo   [OK] 后端服务运行正常
)

:: ======== 第4步：启动前端应用 ========
echo.
echo [4/4] 启动应用程序...

:: 开发模式：在浏览器中打开
echo   [提示] 在浏览器中打开系统...
start http://localhost:8000
echo   [OK] 浏览器已打开

:STARTUP_DONE
echo.
echo ========================================
echo   系统启动成功！
echo ========================================
echo.
echo   访问地址: http://localhost:8000
echo.
echo   默认管理员账号:
echo     用户名: admin
echo     密码:   admin123
echo.
echo   提示:
echo     - 关闭此窗口将停止后端服务（便携版除外）
echo     - 要完全关闭系统，请运行 scripts\关闭系统.bat
echo.

:: 保持窗口打开，监听后端进程（便携版不需要）
if not "%PORTABLE_EXE%"=="" goto :EOF

echo   后端服务运行中，按 Ctrl+C 可停止...
echo.

:: 循环检测后端进程是否存活
:WATCHDOG
if "%START_MODE%"=="packaged" (
    tasklist | findstr "military-rural-backend.exe" >nul 2>&1
) else (
    tasklist | findstr "python.exe" >nul 2>&1
)
if errorlevel 1 (
    echo.
    echo   [警告] 后端进程已退出！
    echo.
    pause
    goto :EOF
)

:: 每5秒检测一次
timeout /t 5 /nobreak >nul
goto :WATCHDOG

endlocal
