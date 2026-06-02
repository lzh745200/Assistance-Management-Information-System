@echo off
REM ========================================
REM 系统状态快速验证脚本
REM ========================================

echo.
echo ========================================
echo 军队乡村振兴管理系统 - 状态验证
echo ========================================
echo.

REM 1. 检查后端服务
echo [1/5] 检查后端服务...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 后端服务运行中 端口8000
) else (
    echo [ERROR] 后端服务未运行
    goto error
)
echo.

REM 2. 检查前端服务
echo [2/5] 检查前端服务...
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 前端服务运行中 端口5173
) else (
    echo [ERROR] 前端服务未运行
    goto error
)
echo.

REM 3. 测试后端健康检查
echo [3/5] 测试后端健康检查...
curl -s http://localhost:8000/api/v1/health | findstr "healthy" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 后端健康检查通过
) else (
    echo [ERROR] 后端健康检查失败
    goto error
)
echo.

REM 4. 验证AI功能
echo [4/5] 验证AI功能...
cd /d "%~dp0backend"
python -c "from app.services.ai.anomaly_detection_service import SKLEARN_AVAILABLE; from app.services.ai.trend_prediction_service import PROPHET_AVAILABLE; exit(0 if (SKLEARN_AVAILABLE and PROPHET_AVAILABLE) else 1)" 2>nul
if %errorlevel% equ 0 (
    echo [OK] AI功能完全可用
) else (
    echo [WARN] AI功能部分可用
)
cd /d "%~dp0"
echo.

REM 5. 测试登录API
echo [5/5] 测试登录API...
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}" ^
  -s | findstr "access_token" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 登录API正常
) else (
    echo [ERROR] 登录API异常
    goto error
)
echo.

echo ========================================
echo [SUCCESS] 系统状态正常
echo ========================================
echo.
echo 访问地址: http://localhost:5173
echo 默认账号: admin / admin123
echo API文档: http://localhost:8000/docs
echo.
echo 提示: 首次登录后请立即修改密码
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo [ERROR] 系统状态异常
echo ========================================
echo.
echo 请运行以下命令诊断问题:
echo   diagnose-and-fix.bat
echo.
echo 或查看服务管理器:
echo   scripts\service-manager.bat status
echo.
pause
exit /b 1
