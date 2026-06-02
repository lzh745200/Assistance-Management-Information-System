@echo off
title 登录问题诊断工具

echo.
echo ========================================
echo 军队乡村振兴管理系统 - 登录问题诊断
echo ========================================
echo.

REM 获取当前目录
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo [1/5] 检查后端服务状态...
echo.

REM 检查后端进程
tasklist | findstr "military-rural-backend.exe" >nul 2>&1
if errorlevel 1 (
    echo [错误] 后端服务未运行
    echo.
    echo 请先启动系统：
    echo   1. 运行"启动系统.bat"
    echo   2. 或手动运行 backend\military-rural-backend.exe
    echo.
    pause
    exit /b 1
) else (
    echo [?] 后端服务正在运行
)

echo.
echo [2/5] 检查端口监听...
echo.

netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [错误] 端口 8000 未监听
    echo 后端服务可能启动失败
    pause
    exit /b 1
) else (
    echo [?] 端口 8000 正在监听
)

echo.
echo [3/5] 测试后端 API...
echo.

REM 测试健康检查
echo 测试: http://localhost:8000/health
curl -s http://localhost:8000/health > temp_health.txt 2>&1
if errorlevel 1 (
    echo [错误] 无法访问健康检查端点
    type temp_health.txt
) else (
    echo [?] 健康检查端点正常
    type temp_health.txt
)
del temp_health.txt >nul 2>&1

echo.
echo 测试: http://localhost:8000/api/v1/auth/login
curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"Admin@2026\"}" > temp_login.txt 2>&1
if errorlevel 1 (
    echo [错误] 登录端点无法访问
    type temp_login.txt
) else (
    echo [?] 登录端点可以访问
    type temp_login.txt
)
del temp_login.txt >nul 2>&1

echo.
echo 测试: http://localhost:8000/api/v1/machine-code/get-machine-code
curl -s http://localhost:8000/api/v1/machine-code/get-machine-code > temp_machine.txt 2>&1
if errorlevel 1 (
    echo [错误] 机器码端点无法访问
    type temp_machine.txt
) else (
    echo [?] 机器码端点可以访问
    type temp_machine.txt
)
del temp_machine.txt >nul 2>&1

echo.
echo [4/5] 检查前端文件...
echo.

if exist "frontend\dist\index.html" (
    echo [?] 前端文件存在
) else (
    echo [错误] 前端文件不存在
    pause
    exit /b 1
)

echo.
echo [5/5] 检查浏览器访问...
echo.

echo 请在浏览器中访问: http://localhost:8000
echo.
echo 如果出现 404 错误，请检查：
echo   1. 浏览器控制台（F12）查看具体错误
echo   2. 确认访问的 URL 是否正确
echo   3. 查看后端日志文件: logs\app.log
echo.

echo ========================================
echo 常见问题解决方案
echo ========================================
echo.

echo 问题 1: 登录时提示 404
echo 原因: 后端 API 路由未正确配置或后端未启动
echo 解决:
echo   1. 确认后端服务正在运行
echo   2. 检查浏览器访问的是 http://localhost:8000 而不是其他地址
echo   3. 清除浏览器缓存（Ctrl+Shift+Delete）
echo   4. 重新启动系统
echo.

echo 问题 2: 获取机器码出现 404
echo 原因: 机器码 API 端点不存在或路径错误
echo 解决:
echo   1. 检查后端日志: logs\app.log
echo   2. 确认后端版本是否支持机器码功能
echo   3. 联系技术支持
echo.

echo 问题 3: 页面完全无法访问
echo 原因: 后端服务未启动或端口被占用
echo 解决:
echo   1. 运行"启动系统.bat"
echo   2. 检查端口 8000 是否被其他程序占用
echo   3. 查看防火墙设置
echo.

echo ========================================
echo 手动测试步骤
echo ========================================
echo.

echo 1. 打开浏览器，访问: http://localhost:8000
echo 2. 打开浏览器开发者工具（F12）
echo 3. 切换到"网络"(Network)标签
echo 4. 尝试登录
echo 5. 查看失败的请求：
echo    - 请求 URL 是什么？
echo    - 状态码是多少？
echo    - 响应内容是什么？
echo.

echo 6. 将以上信息提供给技术支持
echo.

echo ========================================
echo 快速修复
echo ========================================
echo.

echo 如果以上检查都正常但仍然无法登录，尝试：
echo.
echo 1. 完全关闭系统
set /p close="   是否现在关闭系统？(Y/N): "
if /i "%close%"=="Y" (
    echo.
    echo 正在关闭系统...
    taskkill /F /IM military-rural-backend.exe >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo 2. 清除浏览器缓存
echo    - Chrome/Edge: Ctrl+Shift+Delete
echo    - Firefox: Ctrl+Shift+Delete
echo    - 选择"缓存的图片和文件"
echo    - 点击"清除数据"
echo.

echo 3. 重新启动系统
echo    - 运行"启动系统.bat"
echo.

echo 4. 如果问题仍然存在
echo    - 查看日志文件: logs\app.log
echo    - 联系技术支持
echo    - 邮箱: support@military-rural-system.internal
echo.

pause
