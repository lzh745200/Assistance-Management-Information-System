@echo off
REM 后端代码质量检测脚本 (Windows)
REM 用法: scripts\check-backend-quality.bat

echo =========================================
echo 后端代码质量检测开始
echo =========================================
echo.

cd /d "%~dp0\..\backend"

REM 检查虚拟环境
if not exist ".venv" (
    echo ? 错误: 未找到虚拟环境，请先运行: python -m venv .venv
    exit /b 1
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查开发依赖
echo ?? 检查开发依赖...
pip show bandit >nul 2>&1
if errorlevel 1 (
    echo ??  开发依赖未安装，正在安装...
    pip install -r requirements-dev.txt
)
echo ? 开发依赖已就绪
echo.

REM 创建报告目录
set REPORT_DIR=quality-reports
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo =========================================
echo 1. 代码格式检查 (Black)
echo =========================================
black --check app/
echo.

echo =========================================
echo 2. 导入排序检查 (isort)
echo =========================================
isort --check-only app/
echo.

echo =========================================
echo 3. 代码风格检查 (Flake8)
echo =========================================
flake8 app/ --max-line-length=120 --statistics --output-file="%REPORT_DIR%\flake8_%TIMESTAMP%.txt"
echo ?? 报告已保存: %REPORT_DIR%\flake8_%TIMESTAMP%.txt
echo.

echo =========================================
echo 4. 类型检查 (MyPy)
echo =========================================
mypy app/ --ignore-missing-imports --no-strict-optional > "%REPORT_DIR%\mypy_%TIMESTAMP%.txt" 2>&1
echo ?? 报告已保存: %REPORT_DIR%\mypy_%TIMESTAMP%.txt
echo.

echo =========================================
echo 5. 代码质量检查 (Pylint)
echo =========================================
pylint app/ --rcfile=.pylintrc > "%REPORT_DIR%\pylint_%TIMESTAMP%.txt" 2>&1
echo ?? 报告已保存: %REPORT_DIR%\pylint_%TIMESTAMP%.txt
echo.

echo =========================================
echo 6. 安全漏洞扫描 (Bandit)
echo =========================================
bandit -r app/ -f json -o "%REPORT_DIR%\bandit_%TIMESTAMP%.json"
bandit -r app/ -f txt -o "%REPORT_DIR%\bandit_%TIMESTAMP%.txt"
echo ?? 报告已保存: %REPORT_DIR%\bandit_%TIMESTAMP%.txt
echo.

echo =========================================
echo 7. 依赖安全检查 (Safety)
echo =========================================
safety check --json > "%REPORT_DIR%\safety_%TIMESTAMP%.json" 2>&1
safety check > "%REPORT_DIR%\safety_%TIMESTAMP%.txt" 2>&1
echo ?? 报告已保存: %REPORT_DIR%\safety_%TIMESTAMP%.txt
echo.

echo =========================================
echo 8. 依赖审计 (pip-audit)
echo =========================================
pip-audit --format json > "%REPORT_DIR%\pip-audit_%TIMESTAMP%.json" 2>&1
pip-audit > "%REPORT_DIR%\pip-audit_%TIMESTAMP%.txt" 2>&1
echo ?? 报告已保存: %REPORT_DIR%\pip-audit_%TIMESTAMP%.txt
echo.

echo =========================================
echo 9. 代码复杂度分析 (Radon)
echo =========================================
radon cc app/ -a -s > "%REPORT_DIR%\radon_cc_%TIMESTAMP%.txt"
radon mi app/ -s > "%REPORT_DIR%\radon_mi_%TIMESTAMP%.txt"
echo ?? 报告已保存: %REPORT_DIR%\radon_cc_%TIMESTAMP%.txt
echo.

echo =========================================
echo 10. 测试覆盖率
echo =========================================
pytest tests/ --cov=app --cov-report=html --cov-report=term > "%REPORT_DIR%\coverage_%TIMESTAMP%.txt" 2>&1
echo ?? 报告已保存: %REPORT_DIR%\coverage_%TIMESTAMP%.txt
echo ?? HTML 报告: htmlcov\index.html
echo.

echo =========================================
echo 检测完成！
echo =========================================
echo.
echo ?? 所有报告保存在: %REPORT_DIR%\
echo.
echo ?? 建议:
echo   1. 优先修复高危安全漏洞
echo   2. 提升 Pylint 评分至 8.0 以上
echo   3. 保持测试覆盖率在 80%% 以上
echo   4. 定期更新依赖包修复安全漏洞
echo.

pause
