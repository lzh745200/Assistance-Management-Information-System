@echo off
chcp 65001 >nul
echo ============================================================
echo   帮扶管理信息系统 - 磁盘清理工具
echo ============================================================
echo.
echo  [1] 预览清理内容
echo  [2] 执行清理
echo  [3] 安装每周自动清理任务（管理员权限）
echo  [0] 退出
echo.
set /p choice="请选择: "

if "%choice%"=="1" (
    python "%~dp0cleanup.py"
    pause
) else if "%choice%"=="2" (
    python "%~dp0cleanup.py" --execute
    pause
) else if "%choice%"=="3" (
    echo 需要管理员权限...
    python "%~dp0cleanup.py" --schedule
    pause
) else (
    echo 已取消
)
