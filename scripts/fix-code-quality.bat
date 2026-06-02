@echo off
REM 代码质量修复脚本
REM 运行此脚本以自动修复代码质量问题

echo ========================================
echo 代码质量修复工具
echo ========================================
echo.

REM 检查 Python 环境
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装或不在 PATH 中
    echo 请先安装 Python 3.11+ 并添加到 PATH
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
cd backend
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo 警告: ???拟环境不存在，使用全局 Python
)

REM 安装代码质量工具
echo [3/4] 安装代码质量工具...
pip install black isort flake8 -q

REM 运行代码格式化
echo [4/4] 运行代码格式化...
echo.
echo 正在运行 black (代码格式化)...
python -m black app/ --line-length 120
echo.
echo 正在运行 isort (导入排序)...
python -m isort app/ --profile black
echo.
echo 正在运行 flake8 (代码检查)...
python -m flake8 app/ --max-line-length=120 --extend-ignore=E203,W503

echo.
echo ========================================
echo 代码质量修复完成！
echo ========================================
echo.
echo 修复内容:
echo - 代码格式化 (black)
echo - 导入排序 (isort)
echo - 代码检查 (flake8)
echo.
pause
