@echo off
echo ========================================
echo 后端服务端口清理工具
echo ========================================
echo.

echo 1. 查找占用 8000 端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    tasklist /FI "PID eq %%a" | findstr "%%a"
    echo 正在终止进程 %%a...
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo ? 进程 %%a 已终止
    ) else (
        echo ? 无法终止进程 %%a
    )
)

echo.
echo 2. 等待端口释放...
timeout /t 2 /nobreak >nul

echo.
echo 3. 验证端口是否已释放...
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo ? 端口 8000 仍被占用
    netstat -ano | findstr :8000
) else (
    echo ? 端口 8000 已释放
)

echo.
echo ========================================
echo 清理完成
echo ========================================
pause
