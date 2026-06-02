@echo off
chcp 65001 >nul
echo ========================================
echo 前端组件异常 - 完整修复
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] 停止所有服务...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/5] 清理前端缓存...
cd frontend
if exist "node_modules\.vite" (
    rmdir /s /q "node_modules\.vite"
    echo ✓ Vite 缓存已清理
)
cd ..

echo [3/5] 启动后端服务...
cd backend
start /b cmd /c "python start.py > logs\startup.log 2>&1"
cd ..
timeout /t 5 /nobreak >nul

echo [4/5] 启动前端服务...
cd frontend
start /b cmd /c "npm run dev > ../logs/frontend.log 2>&1"
cd ..
timeout /t 3 /nobreak >nul

echo [5/5] 验证服务状态...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo ✗ 后端服务启动失败
) else (
    echo ✓ 后端服务正常
)

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo 修复完成
echo ========================================
echo.
echo 请访问以下地址:
echo   - http://127.0.0.1:5173/
echo   - http://127.0.0.1:5174/
echo   - http://127.0.0.1:5175/
echo.
echo 如果页面仍有问题:
echo   1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo   2. 硬刷新页面（Ctrl+F5）
echo   3. 检查浏览器控制台（F12）
echo.
pause
