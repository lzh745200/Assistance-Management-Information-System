@echo off
chcp 65001 >nul
title 停止军队乡村振兴系统

echo ========================================
echo   停止军队乡村振兴系统
echo ========================================
echo.

echo 正在停止后端服务 (端口 8000)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo   停止进程 %%a...
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo 正在停止前端服务 (端口 5173)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    echo   停止进程 %%a...
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo ========================================
echo   所有服务已停止
echo ========================================
echo.
timeout /t 2 /nobreak >nul
