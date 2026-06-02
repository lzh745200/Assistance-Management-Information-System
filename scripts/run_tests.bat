@echo off
echo ========================================
echo 军队乡村振兴管理系统 - 综合测试执行
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/5] 检查测试环境...
if not exist ".venv\Scripts\python.exe" (
    echo 错误：虚拟环境不存在
    exit /b 1
)

echo [2/5] 检查测试依赖...
.venv\Scripts\python.exe -m pip show pytest >nul 2>&1
if errorlevel 1 (
    echo 安装 pytest...
    .venv\Scripts\python.exe -m pip install pytest pytest-html psutil -q
)

echo [3/5] 执行数据安全测试...
.venv\Scripts\python.exe -m pytest ..\tests\security\test_data_security.py -v --tb=short -m "not slow" 2>&1

echo.
echo [4/5] 执行安全测试...
.venv\Scripts\python.exe -m pytest ..\tests\security\test_security.py -v --tb=short 2>&1

echo.
echo [5/5] 执行 UI/UX 测试...
.venv\Scripts\python.exe -m pytest ..\tests\ui-ux\test_ui_ux.py -v --tb=short 2>&1

echo.
echo [6/7] 执行稳定性测试（排除长稳和压力测试）...
.venv\Scripts\python.exe -m pytest ..\tests\stability\test_stability.py -v --tb=short -m "not slow and not stress" 2>&1

echo.
echo [7/7] 生成测试报告...
.venv\Scripts\python.exe -m pytest ..\tests\ -v --html=..\test_report.html --self-contained-html -m "not slow and not stress" 2>&1

echo.
echo ========================================
echo 测试执行完成！
echo 测试报告：test_report.html
echo ========================================
pause
