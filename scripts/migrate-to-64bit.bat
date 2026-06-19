@echo off
chcp 65001 >/dev/null 2>&1
title 帮扶管理信息系统 - 64-bit Python 迁移

echo ========================================
echo   64-bit Python 迁移脚本
echo ========================================
echo.

set "PYTHON64=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
set "BACKEND_DIR=%~dp0..\backend"

if not exist "%PYTHON64%" (
    echo [错误] 未找到 64-bit Python: %PYTHON64%
    echo 请先安装 Python 3.11 64-bit: https://www.python.org/downloads/
    pause & exit /b 1
)

echo [1/3] 检查 64-bit Python...
"%PYTHON64%" --version
echo [OK]

echo [2/3] 备份旧虚拟环境...
if exist "%BACKEND_DIR%\.venv" (
    if exist "%BACKEND_DIR%\.venv.bak" rmdir /s /q "%BACKEND_DIR%\.venv.bak"
    move "%BACKEND_DIR%\.venv" "%BACKEND_DIR%\.venv.bak"
    echo [OK] 已备份到 .venv.bak
) else (
    echo [OK] 无现有虚拟环境
)

echo [3/3] 创建 64-bit 虚拟环境并安装依赖...
cd /d "%BACKEND_DIR%"
"%PYTHON64%" -m venv .venv
call .venv\Scripts\activate
pip install --upgrade pip -q
pip install -r requirements.txt
echo [OK] 64-bit 迁移完成

echo.
echo ========================================
echo   迁移成功！
echo ========================================
echo   新 Python: 64-bit
echo   删除旧环境: rmdir /s /q backend\.venv.bak
echo.
pause
