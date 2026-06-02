@echo off
REM ========================================
REM 后端服务启动脚本（清理版）
REM 确保停止所有旧进程并启动新服务
REM ========================================

echo.
echo ========================================
echo 军队乡村振兴管理系统 - 后端启动
echo ========================================
echo.

REM 1. 停止所有旧的Python进程
echo [1/4] 停止旧的后端进程...
taskkill /F /IM python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 已停止旧进程
    timeout /t 3 /nobreak >nul
) else (
    echo [INFO] 没有运行中的进程
)
echo.

REM 2. 验证依赖包
echo [2/4] 验证AI依赖包...
cd /d "%~dp0backend"
python -c "from app.services.ai.anomaly_detection_service import SKLEARN_AVAILABLE; from app.services.ai.trend_prediction_service import PROPHET_AVAILABLE; exit(0 if (SKLEARN_AVAILABLE and PROPHET_AVAILABLE) else 1)" 2>nul
if %errorlevel% equ 0 (
    echo [OK] AI依赖包已安装 (scikit-learn + Prophet)
) else (
    echo [WARN] AI依赖包未完全安装，正在安装...
    pip install -r requirements.txt --upgrade
)
cd /d "%~dp0"
echo.

REM 3. 启动后端服务
echo [3/4] 启动后端服务...
cd /d "%~dp0backend"
start "后端服务" /MIN python start.py
timeout /t 5 /nobreak >nul
cd /d "%~dp0"
echo.

REM 4. 验证服务状态
echo [4/4] 验证服务状态...
timeout /t 3 /nobreak >nul
netstat -ano | findstr ":8000" | findstr "LISTENING" | findstr "0.0.0.0" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 后端服务启动成功
    echo.
    echo ========================================
    echo 服务信息
    echo ========================================
    echo 后端地址: http://localhost:8000
    echo API文档: http://localhost:8000/docs
    echo 健康检查: http://localhost:8000/api/v1/health
    echo.
    echo 提示: 窗口最小化运行，关闭窗口将停止服务
    echo ========================================
) else (
    echo [ERROR] 后端服务启动失败
    echo.
    echo 请检查:
    echo 1. 端口8000是否被占用
    echo 2. Python环境是否正确
    echo 3. 依赖包是否完整安装
    echo.
    echo 查看详细日志: backend\logs\app.log
    pause
    exit /b 1
)
echo.
