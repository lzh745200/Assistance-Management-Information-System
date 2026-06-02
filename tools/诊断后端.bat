@echo off
chcp 65001 >nul
echo ========================================
echo 后端完整诊断和修复
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] 检查后端进程...
tasklist | findstr python >nul 2>&1
if errorlevel 1 (
    echo ✗ 后端未运行
    echo   正在启动后端...
    start /b cmd /c "cd backend && python start.py > logs\startup.log 2>&1"
    timeout /t 5 /nobreak >nul
) else (
    echo ✓ 后端进程运行中
)

echo.
echo [2/6] 检查端口占用...
netstat -ano | findstr :8000 >nul 2>&1
if errorlevel 1 (
    echo ✗ 端口 8000 未监听
) else (
    echo ✓ 端口 8000 正常监听
)

echo.
echo [3/6] 测试健康检查...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo ✗ 健康检查失败
) else (
    echo ✓ 健康检查通过
)

echo.
echo [4/6] 测试登录...
python backend\test_backend_monitor.py >nul 2>&1
if errorlevel 1 (
    echo ⚠ 部分测试失败（查看详细日志）
) else (
    echo ✓ 所有测试通过
)

echo.
echo [5/6] 检查日志文件...
if exist "backend\logs\app.log" (
    echo ✓ 应用日志存在
) else (
    echo ✗ 应用日志不存在
)

if exist "backend\logs\error.log" (
    for %%A in ("backend\logs\error.log") do set size=%%~zA
    if !size! gtr 0 (
        echo ⚠ 错误日志有内容 (!size! 字节)
    ) else (
        echo ✓ 错误日志为空
    )
) else (
    echo ✗ 错误日志不存在
)

echo.
echo [6/6] 检查数据库...
if exist "backend\data\rural_revitalization.db" (
    echo ✓ 数据库文件存在
) else (
    echo ✗ 数据库文件不存在
)

echo.
echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 详细测试报告:
python backend\test_backend_monitor.py
echo.
echo 查看日志: 查看后端日志.bat
echo 启动系统: scripts\start-all.bat
echo.
pause
