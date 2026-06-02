@echo off
setlocal enabledelayedexpansion

REM ========================================
REM 军队乡村振兴管理系统 - 快速启动
REM ========================================

REM 获取版本号（从 package.json 读取）
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" package.json 2^>nul') do (
    set "VER_RAW=%%~a"
    set "VERSION=!VER_RAW:"=!"
)
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "VERSION=%%v"
)
if not defined VERSION set "VERSION=1.1.0"

title 军队乡村振兴管理系统 v!VERSION!

echo ========================================
echo 军队乡村振兴管理系统 v!VERSION!
echo ========================================
echo.

REM 获取项目根目录
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

REM ========================================
REM 检查后端状态
REM ========================================
echo [检查] 验证后端服务...

REM 检查端口占用
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    REM 端口被占用，检查是否是后端服务
    curl -s http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo [?] 后端服务已在运行
        echo [启动] 打开应用程序...
        goto :START_APP
    ) else (
        echo [警告] 端口 8000 被其他程序占用
        echo.
        echo 请选择操作:
        echo   1. 尝试关闭占用进程
        echo   2. 继续（可能失败）
        echo   3. 退出
        echo.
        set /p choice="请输入选择 (1-3): "

        if "!choice!"=="1" (
            for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
                echo [关闭] 进程 ID: %%a
                taskkill /F /PID %%a >nul 2>&1
            )
            timeout /t 2 >nul
        ) else if "!choice!"=="3" (
            exit /b 0
        )
    )
) else (
    echo [?] 端口 8000 可用
)

REM ========================================
REM 启动后端
REM ========================================
echo.
echo [启动] 后端服务...

REM 检查打包后端
if exist "dist\backend\windows\military-rural-backend.exe" (
    start "军队乡村振兴管理系统-后端" /B "dist\backend\windows\military-rural-backend.exe"
    echo [?] 打包后端程序已启动
    goto :WAIT_BACKEND
)

REM 检查 resources 后端
if exist "resources\backend\military-rural-backend.exe" (
    start "军队乡村振兴管理系统-后端" /B "resources\backend\military-rural-backend.exe"
    echo [?] Resources 后端程序已启动
    goto :WAIT_BACKEND
)

REM 开发模式：使用 Python
echo [提示] 未找到打包后端，使用开发模式...
cd /d "%PROJECT_DIR%\backend"
if exist ".venv\Scripts\activate.bat" (
    start "军队乡村振兴管理系统-后端" cmd /k "call .venv\Scripts\activate.bat && python start.py"
) else (
    start "军队乡村振兴管理系统-后端" cmd /k "python start.py"
)

:WAIT_BACKEND

REM 等待后端启动
echo [等待] 后端服务初始化（最多 30 秒）...
for /L %%i in (1,1,30) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo [?] 后端服务已就绪
        goto :BACKEND_READY
    )
    timeout /t 1 >nul
)
echo [警告] 后端服务启动超时，继续...

:BACKEND_READY

REM ========================================
REM 启动应用程序
REM ========================================
:START_APP
echo.
echo [启动] 应用程序...

if exist "dist\win-unpacked\军队乡村振兴管理系统.exe" (
    start "" "dist\win-unpacked\军队乡村振兴管理系统.exe"
    echo [?] 应用程序已启动
    echo.
    echo ========================================
    echo 系统已启动
    echo ========================================
    echo.
    echo 访问地址: http://localhost:8000
    echo.
    echo 提示:
    echo   - 管理员账号请查看后端服务窗口
    echo   - 关闭此窗口不会停止服务
    echo   - 请在应用程序中操作
    echo.
    pause
) else (
    REM 查找 Portable 版本
    for /f "delims=" %%F in ('dir /b /o-n "dist\*Portable*.exe" 2^>nul ^| findstr /i "军队乡村振兴管理系统"') do (
        echo [提示] 请双击以下文件启动完整应用程序:
        echo.
        echo   dist\%%F
        echo.
        echo 或者访问:
        echo   http://localhost:8000
        echo.
        pause
        goto :ENDLOCAL
    )

    REM 仅启动后端，打开浏览器
    echo [提示] 未找到打包程序，仅启动后端服务
    echo.
    start http://localhost:8000
    echo.
    echo ========================================
    echo 后端已启动
    echo ========================================
    echo.
    echo 访问地址: http://localhost:8000
    echo.
    echo 提示:
    echo   - 管理员账号请查看后端服务窗口
    echo   - 浏览器已打开访问地址
    echo   - 关闭此窗口会停止后端服务
    echo.
    pause
)

:ENDLOCAL
endlocal
