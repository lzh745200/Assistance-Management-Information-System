@echo off
title 后端服务 - 军队乡村振兴管理系统

cd /d "%~dp0..\backend"

echo ========================================
echo 军队全面推进乡村振兴工作管理系统
echo 后端服务启动中...
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" start.py
) else (
    python start.py
)

pause
