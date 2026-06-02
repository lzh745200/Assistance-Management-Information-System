@echo off
REM ========================================
REM AI依赖状态检查脚本
REM ========================================

echo.
echo ========================================
echo AI依赖状态检查
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] 检查依赖包安装状态...
python -c "import sklearn; import prophet; print('✅ 依赖包已安装: scikit-learn', sklearn.__version__, '+ Prophet', prophet.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 依赖包未安装或导入失败
    echo.
    echo 请运行: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.

echo [2/3] 检查AI服务模块状态...
python -c "import sys; sys.path.insert(0, '.'); from app.services.ai.anomaly_detection_service import SKLEARN_AVAILABLE; from app.services.ai.trend_prediction_service import PROPHET_AVAILABLE; print('✅ 异常检测服务:', 'True' if SKLEARN_AVAILABLE else 'False'); print('✅ 趋势预测服务:', 'True' if PROPHET_AVAILABLE else 'False'); exit(0 if (SKLEARN_AVAILABLE and PROPHET_AVAILABLE) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] AI服务模块加载失败
    pause
    exit /b 1
)
echo.

echo [3/3] 运行完整测试...
python test_ai_dependencies.py
if %errorlevel% neq 0 (
    echo [ERROR] AI功能测试失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] AI依赖完全正常
echo ========================================
echo.
pause
