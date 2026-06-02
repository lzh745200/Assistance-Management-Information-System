@echo off
cd /d "%~dp0..\backend"

echo 正在构建后端...
echo.

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 错误: 无法激活虚拟环境
    exit /b 1
)

python -m PyInstaller military-rural-backend-full.spec --clean --noconfirm
if errorlevel 1 (
    echo 错误: 构建失败
    exit /b 1
)

echo.
echo 构建完成！
if exist "dist\military-rural-backend.exe" (
    echo 文件位置: backend\dist\military-rural-backend.exe
    for %%A in ("dist\military-rural-backend.exe") do echo 文件大小: %%~zA 字节
) else (
    echo 错误: 未找到生成的文件
    exit /b 1
)
