@echo off
REM ========================================
REM 后端服务问题诊断和修复脚本
REM ========================================

echo.
echo ========================================
echo 后端服务诊断和修复
echo ========================================
echo.

REM 1. 检查服务状态
echo [1/6] 检查服务状态...
netstat -ano | findstr ":8000" | findstr "LISTENING"
if %errorlevel% equ 0 (
    echo [OK] 后端端口8000已监听
) else (
    echo [ERROR] 后端端口8000未监听
)

netstat -ano | findstr ":5173" | findstr "LISTENING"
if %errorlevel% equ 0 (
    echo [OK] 前端端口5173已监听
) else (
    echo [ERROR] 前端端口5173未监听
)
echo.

REM 2. 测试后端健康检查
echo [2/6] 测试后端健康检查...
curl -s http://localhost:8000/api/v1/health
echo.
echo.

REM 3. 测试后端登录API
echo [3/6] 测试后端登录API...
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}" ^
  -s | findstr "access_token"
if %errorlevel% equ 0 (
    echo [OK] 后端登录API正常
) else (
    echo [ERROR] 后端登录API异常
)
echo.

REM 4. 测试前端访问
echo [4/6] 测试前端访问...
curl -s http://localhost:5173 | findstr "军队"
if %errorlevel% equ 0 (
    echo [OK] 前端页面正常
) else (
    echo [ERROR] 前端页面异常
)
echo.

REM 5. 检查后端配置
echo [5/6] 检查后端配置...
cd /d "%~dp0..\backend"
findstr "^HOST=" .env
findstr "^PORT=" .env
findstr "^CORS_ORIGINS=" .env
echo.

REM 6. 提供解决方案
echo [6/6] 诊断完成
echo.
echo ========================================
echo 解决方案
echo ========================================
echo.
echo 如果后端API正常但前端仍然401错误，请：
echo.
echo 1. 打开浏览器开发者工具（F12）
echo 2. 切换到Network标签
echo 3. 尝试登录
echo 4. 查看失败的请求：
echo    - 请求URL是什么？
echo    - 状态码是多少？
echo    - 响应内容是什么？
echo.
echo 5. 检查Console标签是否有错误
echo.
echo 常见问题：
echo - 如果请求URL是 http://localhost:5173/api/v1/auth/login
echo   说明Vite代理未生效，需要重启前端
echo.
echo - 如果请求URL是 http://localhost:8000/api/v1/auth/login
echo   说明代理正常，检查CORS配置
echo.
echo - 如果看到 ERR_CONNECTION_REFUSED
echo   说明后端未运行或端口错误
echo.
echo 重启服务：
echo   1. 停止所有服务: Ctrl+C
echo   2. 重新启动后端: start-backend.bat
echo   3. 重新启动前端: start-frontend.bat
echo.
pause
