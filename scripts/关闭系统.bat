@echo off
title 关闭军队乡村振兴管理系统

echo.
echo ========================================
echo 关闭军队乡村振兴管理系统
echo ========================================
echo.

echo [检查] 查找运行中的后端进程...

REM 查找后端进程
tasklist | findstr "military-rural-backend.exe" >nul 2>&1
if errorlevel 1 (
    echo [提示] 未发现运行中的后端进程
    echo.
    pause
    exit /b 0
)

echo [发现] 后端进程正在运行
echo.

REM 显示进程信息
for /f "tokens=2" %%a in ('tasklist ^| findstr "military-rural-backend.exe"') do (
    echo 进程 ID: %%a
)

echo.
echo 确认要关闭系统吗？
echo.
set /p confirm="输入 Y 确认，其他键取消: "

if /i not "%confirm%"=="Y" (
    echo.
    echo [取消] 操作已取消
    pause
    exit /b 0
)

echo.
echo [关闭] 正在关闭后端服务...

REM 关闭所有后端进程
taskkill /F /IM military-rural-backend.exe >nul 2>&1

if errorlevel 1 (
    echo [错误] 关闭进程失败
    echo 请手动在任务管理器中结束进程
) else (
    echo [?] 后端服务已关闭
)

echo.
echo ========================================
echo 系统已关闭
echo ========================================
echo.
pause
