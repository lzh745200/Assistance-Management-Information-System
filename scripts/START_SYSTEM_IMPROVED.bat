@echo off
chcp 65001 >nul
title 军队乡村振兴系统启动器 (改进版)
color 0A

echo ========================================
echo   军队乡村振兴系统启动器
echo   版本: 2.0 (优化版)
echo ========================================
echo.

REM 检查Python是否安装
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo [成功] Python环境正常
python --version
echo.

REM 检查Node.js是否安装
echo [2/5] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)
echo [成功] Node.js环境正常
node --version
echo.

REM 检查并启动Redis（可选）
echo [3/5] 检查Redis服务...
where redis-server >nul 2>&1
if %errorlevel% equ 0 (
    echo [提示] 检测到Redis已安装
    set /p redis_choice="是否启动Redis服务? (Y/N): "
    if /i "%redis_choice%"=="Y" (
        echo 正在启动Redis...
        start "Redis服务" redis-server
        timeout /t 2 /nobreak >nul
        echo [成功] Redis已启动
    ) else (
        echo [提示] 将使用内存缓存替代Redis
    )
) else (
    echo [提示] Redis未安装，将使用内存缓存
    echo [信息] 运行 start_redis.bat 安装或启动Redis
)
echo.

REM 安装后端依赖
echo [4/5] 准备后端环境...
cd backend
if not exist "venv" (
    echo 正在创建Python虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 检查并安装Python依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 后端依赖安装失败，可能影响系统运行
) else (
    echo [成功] Python依赖就绪
)
cd ..
echo.

REM 安装前端依赖
echo [5/5] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 正在安装前端依赖，首次可能需要几分钟...
    call npm install
) else (
    echo [成功] 前端依赖已存在
)
cd ..
echo.

echo ========================================
echo   系统初始化完成！
echo ========================================
echo.
echo 请选择启动方式：
echo.
echo   1. 仅启动后端服务
echo   2. 仅启动前端服务
echo   3. 同时启动前后端（推荐）
echo   4. 启动Redis服务
echo   5. 检查系统状态
echo   6. 退出
echo.
set /p choice="请输入选项 (1-6): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_all
if "%choice%"=="4" goto start_redis
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto end
goto invalid_choice

:start_backend
echo.
echo ========================================
echo   正在启动后端服务...
echo ========================================
echo.
cd backend
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto end

:start_frontend
echo.
echo ========================================
echo   正在启动前端服务...
echo ========================================
echo.
cd frontend
call npm run dev
goto end

:start_all
echo.
echo ========================================
echo   正在启动前后端服务...
echo ========================================
echo.
echo [后端] 启动中...
start "后端服务" cmd /k "cd backend && venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [前端] 启动中...
timeout /t 3 /nobreak >nul
start "前端服务" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo.
echo API文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo.
echo 默认账号:
echo   用户名: admin
echo   密码:   请查看后端服务窗口的启动日志
echo.
echo 系统正在启动，浏览器将自动打开...
timeout /t 2 /nobreak >nul
start http://localhost:5173

goto end

:start_redis
echo.
echo ========================================
echo   正在启动Redis服务...
echo ========================================
echo.
where redis-server >nul 2>&1
if %errorlevel% equ 0 (
    start "Redis服务" redis-server
    echo [成功] Redis服务已启动
) else (
    echo [错误] Redis未安装
    echo [信息] 请运行 start_redis.bat 安装Redis
)
goto end

:check_status
echo.
echo ========================================
echo   检查系统状态...
echo ========================================
echo.
call check_system_status.bat
goto end

:invalid_choice
echo.
echo [错误] 无效的选项，请重新运行脚本
pause
exit /b 1

:end
echo.
echo 感谢使用，再见！
pause >nul
