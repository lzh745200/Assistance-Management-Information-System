@echo off
chcp 65001 >nul
echo ==========================================
echo 测试 401 登录错误修复
echo ==========================================
echo.

echo 1. 测试后端登录接口...
curl -X POST http://127.0.0.1:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"Admin@2026\"}" ^
  -s -o response.json -w "%%{http_code}" > http_code.txt

set /p HTTP_CODE=<http_code.txt

if "%HTTP_CODE%"=="200" (
  echo ✅ 后端登录接口正常 ^(HTTP 200^)
  type response.json
) else (
  echo ❌ 后端登录接口异常 ^(HTTP %HTTP_CODE%^)
  type response.json
  del response.json http_code.txt
  pause
  exit /b 1
)

echo.
echo ==========================================
echo 测试完成
echo ==========================================
echo.
echo 修复已完成！现在请：
echo 1. 访问 http://localhost:5173/clear-auth.html 清除缓存
echo 2. 或在浏览器控制台执行：
echo    sessionStorage.clear^(^); localStorage.clear^(^); location.reload^(^);
echo 3. 重新登录
echo.

del response.json http_code.txt 2>nul
pause
