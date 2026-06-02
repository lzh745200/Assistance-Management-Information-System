@echo off
REM ========================================
REM 军队乡村振兴管理系统 - 服务管理脚本
REM 版本: 1.0.4
REM 功能: 启动、停止、重启、状态检查
REM ========================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

REM 颜色定义
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

if "%1"=="" goto :show_usage
if "%1"=="start" goto :start_services
if "%1"=="stop" goto :stop_services
if "%1"=="restart" goto :restart_services
if "%1"=="status" goto :check_status
if "%1"=="logs" goto :show_logs
if "%1"=="diagnose" goto :diagnose
goto :show_usage

:show_usage
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%军队乡村振兴管理系统 - 服务管理%RESET%
echo %BLUE%========================================%RESET%
echo.
echo 用法: service-manager.bat [命令]
echo.
echo 命令:
echo   start      - 启动前后端服务
echo   stop       - 停止所有服务
echo   restart    - 重启所有服务
echo   status     - 检查服务状态
echo   logs       - 查看服务日志
echo   diagnose   - 诊断服务问题
echo.
echo 示例:
echo   service-manager.bat start
echo   service-manager.bat status
echo.
goto :eof

:start_services
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%启动服务%RESET%
echo %BLUE%========================================%RESET%
echo.

REM 检查后端是否已运行
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo %YELLOW%[警告] 后端服务已在运行（端口8000）%RESET%
    echo.
) else (
    echo %GREEN%[1/2] 启动后端服务...%RESET%
    cd backend

    REM 检查Python环境
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo %RED%[错误] 未找到Python，请先安装Python 3.11%RESET%
        goto :eof
    )

    REM 检查虚拟环境
    if not exist "venv" (
        echo %YELLOW%[提示] 创建虚拟环境...%RESET%
        python -m venv venv
    )

    REM 激活虚拟环境并启动
    call venv\Scripts\activate.bat

    REM 检查依赖
    python -c "import fastapi" >nul 2>&1
    if !errorlevel! neq 0 (
        echo %YELLOW%[提示] 安装依赖...%RESET%
        pip install -r requirements.txt
    )

    REM 后台启动
    start "后端服务" /MIN python start.py

    REM 等??启动
    timeout /t 3 /nobreak >nul

    REM 验证启动
    curl -s http://localhost:8000/api/v1/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[成功] 后端服务启动成功 (http://localhost:8000)%RESET%
    ) else (
        echo %RED%[错误] 后端服务启动失败%RESET%
    )

    cd ..
    echo.
)

REM 检查前端是否已运行
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo %YELLOW%[警告] 前端服务已在运行（端口5173）%RESET%
    echo.
) else (
    echo %GREEN%[2/2] 启动前端服务...%RESET%
    cd frontend

    REM 检查Node.js环境
    node --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo %RED%[错误] 未找到Node.js，请先安装Node.js%RESET%
        goto :eof
    )

    REM 检查依赖
    if not exist "node_modules" (
        echo %YELLOW%[提示] 安装依赖...%RESET%
        call npm install
    )

    REM 后台启动
    start "前端服务" /MIN npm run dev

    REM 等待启动
    timeout /t 5 /nobreak >nul

    REM 验证启动
    curl -s http://localhost:5173 >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[成功] 前端服务启动成功 (http://localhost:5173)%RESET%
    ) else (
        echo %YELLOW%[提示] 前端服务可能需要更多时间启动%RESET%
    )

    cd ..
    echo.
)

echo %GREEN%========================================%RESET%
echo %GREEN%服务启动完成%RESET%
echo %GREEN%========================================%RESET%
echo.
echo 访问地址:
echo   前端: http://localhost:5173
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
echo 默认管理员账号:
echo   用户名: admin
echo   密码: admin123
echo.
echo %YELLOW%提示: 首次登录后请立即修改密码！%RESET%
echo.
goto :eof

:stop_services
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%停止服务%RESET%
echo %BLUE%========================================%RESET%
echo.

REM 停止后端服务
echo %YELLOW%[1/2] 停止后端服务...%RESET%
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[成功] 后端服务已停止 (PID: %%a)%RESET%
    )
)

REM 停止前端服务
echo %YELLOW%[2/2] 停止前端服务...%RESET%
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%[成功] 前端服务已停止 (PID: %%a)%RESET%
    )
)

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%服务停止完成%RESET%
echo %GREEN%========================================%RESET%
echo.
goto :eof

:restart_services
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%重启服务%RESET%
echo %BLUE%========================================%RESET%
echo.
call :stop_services
timeout /t 2 /nobreak >nul
call :start_services
goto :eof

:check_status
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%服务状态检查%RESET%
echo %BLUE%========================================%RESET%
echo.

REM 检查后端
echo %YELLOW%[后端服务]%RESET%
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        echo   状态: %GREEN%运行中%RESET%
        echo   端口: 8000
        echo   PID: %%a
    )

    REM 健康检查
    curl -s http://localhost:8000/api/v1/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo   健康: %GREEN%正常%RESET%
    ) else (
        echo   健康: %RED%异常%RESET%
    )
) else (
    echo   状态: %RED%未运行%RESET%
)
echo.

REM 检查前端
echo %YELLOW%[前端服务]%RESET%
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
        echo   状态: %GREEN%运行中%RESET%
        echo   端口: 5173
        echo   PID: %%a
    )
) else (
    echo   状态: %RED%未运行%RESET%
)
echo.

REM 检查数据库
echo %YELLOW%[数据库]%RESET%
if exist "backend\data\rural_revitalization.db" (
    for %%a in ("backend\data\rural_revitalization.db") do (
        echo   状态: %GREEN%正常%RESET%
        echo   大小: %%~za 字节
        echo   路径: backend\data\rural_revitalization.db
    )
) else (
    echo   状态: %RED%未找到%RESET%
)
echo.

echo %BLUE%========================================%RESET%
goto :eof

:show_logs
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%服务日志%RESET%
echo %BLUE%========================================%RESET%
echo.

if exist "backend\logs\app.log" (
    echo %YELLOW%[后端日志] (最近20行)%RESET%
    powershell -Command "Get-Content backend\logs\app.log -Tail 20"
    echo.
) else (
    echo %RED%[错误] 未找到后端日志文件%RESET%
    echo.
)

goto :eof

:diagnose
echo.
echo %BLUE%========================================%RESET%
echo %BLUE%系统诊断%RESET%
echo %BLUE%========================================%RESET%
echo.

REM Python环境
echo %YELLOW%[Python环境]%RESET%
python --version 2>nul
if !errorlevel! neq 0 (
    echo   %RED%未安装Python%RESET%
) else (
    python -c "import sys; print(f'  版本: {sys.version}')"
    python -c "import fastapi; print(f'  FastAPI: {fastapi.__version__}')" 2>nul
    python -c "import uvicorn; print(f'  Uvicorn: {uvicorn.__version__}')" 2>nul
)
echo.

REM Node.js环境
echo %YELLOW%[Node.js环境]%RESET%
node --version 2>nul
if !errorlevel! neq 0 (
    echo   %RED%未安装Node.js%RESET%
) else (
    node --version
    npm --version
)
echo.

REM 端口占用
echo %YELLOW%[端口占用]%RESET%
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   8000: %GREEN%已占用%RESET%
) else (
    echo   8000: %YELLOW%空闲%RESET%
)

netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo   5173: %GREEN%已占用%RESET%
) else (
    echo   5173: %YELLOW%空闲%RESET%
)
echo.

REM 配置文件
echo %YELLOW%[配置文件]%RESET%
if exist "backend\.env" (
    echo   backend\.env: %GREEN%存在%RESET%
) else (
    echo   backend\.env: %RED%缺失%RESET%
)

if exist "frontend\.env.development" (
    echo   frontend\.env.development: %GREEN%存在%RESET%
) else (
    echo   frontend\.env.development: %YELLOW%缺失%RESET%
)
echo.

REM 数据库文件
echo %YELLOW%[数据库文件]%RESET%
if exist "backend\data\rural_revitalization.db" (
    echo   rural_revitalization.db: %GREEN%存在%RESET%
) else (
    echo   rural_revitalization.db: %RED%缺失%RESET%
)
echo.

echo %BLUE%========================================%RESET%
echo %BLUE%诊断完成%RESET%
echo %BLUE%========================================%RESET%
echo.
goto :eof

:eof
