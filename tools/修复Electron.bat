@echo off
chcp 65001 >nul
echo ========================================
echo 修复 Electron 依赖（Windows 版本）
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 清理旧的依赖...
if exist node_modules (
    rmdir /s /q node_modules
)
if exist package-lock.json (
    del /f /q package-lock.json
)

echo.
echo [2/2] 重新安装依赖（Windows 版本）...
call npm install

echo.
echo ========================================
echo ✓ 修复完成！
echo ========================================
echo.
echo 验证安装：
if exist "node_modules\electron\dist\electron.exe" (
    echo ✓ Electron Windows 版本已安装
) else (
    echo ✗ Electron 安装失败，请检查网络连接
)
echo.
echo 现在可以运行: npm run start
echo.
pause
