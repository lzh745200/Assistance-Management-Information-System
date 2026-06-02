@echo off
chcp 65001 >nul
echo ========================================
echo AI依赖完整诊断
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/6] 检查Python版本...
python --version
echo.

echo [2/6] 检查依赖包安装...
python -c "import sklearn, prophet; print('✓ scikit-learn:', sklearn.__version__); print('✓ Prophet:', prophet.__version__)" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 依赖包导入失败
    pause
    exit /b 1
)
echo.

echo [3/6] 检查服务模块...
python -c "import sys; sys.path.insert(0, '.'); from app.services.ai.anomaly_detection_service import SKLEARN_AVAILABLE; from app.services.ai.trend_prediction_service import PROPHET_AVAILABLE; print('✓ SKLEARN_AVAILABLE:', SKLEARN_AVAILABLE); print('✓ PROPHET_AVAILABLE:', PROPHET_AVAILABLE)" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 服务模块加载失败
    pause
    exit /b 1
)
echo.

echo [4/6] 检查后端进程...
tasklist | findstr "python.exe"
echo.

echo [5/6] 检查端口占用...
netstat -ano | findstr ":8000"
echo.

echo [6/6] 检查启动日志...
if exist "final_startup.log" (
    echo 最近的启动日志:
    type final_startup.log | findstr /C:"未安装" /C:"WARNING" /C:"ERROR" /C:"所有关键依赖"
    if %errorlevel% neq 0 (
        echo ✓ 日志中无警告或错误
    )
) else (
    echo 启动日志文件不存在
)
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 如果您仍然看到错误提示，请告诉我：
echo 1. 在哪个窗口看到的？（后端启动窗口/浏览器/其他）
echo 2. 完整的错误信息是什么？
echo 3. 错误是什么时候出现的？
echo.
pause
