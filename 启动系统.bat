@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON="

REM 1. 优先探测 %LOCALAPPDATA% 下的 Python 3.11 安装（含 32/64 位）
if defined LOCALAPPDATA (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311-32\python.exe"
    ) do (
        if not defined PYTHON if exist "%%~P" set "PYTHON=%%~P"
    )
)

REM 2. 回退：通过 where python / where python3 在 PATH 中查找
if not defined PYTHON (
    for /f "delims=" %%W in ('where python 2^>nul') do (
        if not defined PYTHON set "PYTHON=%%W"
    )
)
if not defined PYTHON (
    for /f "delims=" %%W in ('where python3 2^>nul') do (
        if not defined PYTHON set "PYTHON=%%W"
    )
)

if not defined PYTHON (
    echo [ERROR] 未找到 Python 3.11+，请安装 Python 后重试。
    echo   推荐安装路径: %%LOCALAPPDATA%%\Programs\Python\Python311\
    pause
    exit /b 1
)

echo Starting system (Python: %PYTHON%)...
"%PYTHON%" launch.py
pause
