@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 统一启动脚本的 Windows 批处理包装器
REM 调用 Python 启动脚本

cd /d "%~dp0..\.."

REM 查找并激活虚拟环境
set VENV_ACTIVATED=0

if exist "venv_new\Scripts\activate.bat" (
    call venv_new\Scripts\activate.bat
    set VENV_ACTIVATED=1
) else if exist "venv_clean\Scripts\activate.bat" (
    call venv_clean\Scripts\activate.bat
    set VENV_ACTIVATED=1
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set VENV_ACTIVATED=1
) else if exist "backend\.venv\Scripts\activate.bat" (
    call backend\.venv\Scripts\activate.bat
    set VENV_ACTIVATED=1
)

REM 调用 Python 启动脚本
python -m scripts.startup.start %*

REM 保存退出码
set EXIT_CODE=%ERRORLEVEL%

REM 退出
exit /b %EXIT_CODE%
