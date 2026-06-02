@echo off
title API端点测试工具

echo.
echo ========================================
echo 军队乡村振兴管理系统 - API端点测试
echo ========================================
echo.

REM 检查curl是否可用
where curl >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 curl 命令
    echo 请确保 Windows 10 版本 1803 或更高
    pause
    exit /b 1
)

echo [1/6] 测试健康检查端点...
echo.
echo URL: http://localhost:8000/health
curl -v http://localhost:8000/health
echo.
pause

echo.
echo [2/6] 测试根路径...
echo.
echo URL: http://localhost:8000/
curl -v http://localhost:8000/
echo.
pause

echo.
echo [3/6] 测试登录端点（正确密码）...
echo.
echo URL: http://localhost:8000/api/v1/auth/login
echo 用户名: admin
echo 密码: Admin@2026
curl -v -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"Admin@2026\"}"
echo.
pause

echo.
echo [4/6] 测试登录端点（错误密码）...
echo.
echo URL: http://localhost:8000/api/v1/auth/login
echo 用户名: admin
echo 密码: wrongpassword
curl -v -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"wrongpassword\"}"
echo.
pause

echo.
echo [5/6] 测试机器码端点...
echo.
echo URL: http://localhost:8000/api/v1/machine-code/get-machine-code
curl -v http://localhost:8000/api/v1/machine-code/get-machine-code
echo.
pause

echo.
echo [6/6] 测试不存在的端点（应该返回404）...
echo.
echo URL: http://localhost:8000/api/v1/nonexistent
curl -v http://localhost:8000/api/v1/nonexistent
echo.
pause

echo.
echo ========================================
echo 测试完成
echo ========================================
echo.
echo 请检查上面的输出：
echo   - 200 状态码表示成功
echo   - 401 状态码表示认证失败（正常）
echo   - 404 状态码表示端点不存在（问题）
echo   - Connection refused 表示后端未启动
echo.
pause
