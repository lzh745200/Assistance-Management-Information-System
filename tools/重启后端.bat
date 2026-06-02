@echo off
chcp 65001 >nul
echo ========================================
echo 重启后端服务
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] 停止现有后端进程...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] 启动后端服务...
start /b cmd /c "python start.py > logs\startup.log 2>&1"

echo [3/3] 等待服务就绪...
timeout /t 5 /nobreak >nul

echo.
echo 测试服务状态...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo ✗ 后端服务启动失败
    echo   查看日志: type backend\logs\startup.log
) else (
    echo ✓ 后端服务启动成功
    echo.
    echo 可用地址:
    echo   - 健康检查: http://127.0.0.1:8000/health
    echo   - API 文档: http://127.0.0.1:8000/docs
    echo   - 前端界面: http://127.0.0.1:8000/
)

echo.
pause
