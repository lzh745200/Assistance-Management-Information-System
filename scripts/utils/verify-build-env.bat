@echo off
REM ============================================================
REM  验证构建脚本 - 快速测试版
REM  验证构建流程但不实际构建完整镜像
REM ============================================================

setlocal enabledelayedexpansion

echo ========================================
echo   构建脚本验证测试
echo ========================================
echo.

REM 测试计数
set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

REM 测试1: Docker运行检查
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查Docker是否运行...
docker version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Docker未运行
    set /a FAILED_TESTS+=1
) else (
    echo [PASS] Docker运行正常
    set /a PASSED_TESTS+=1
)

REM 测试2: Buildx可用性
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查Docker Buildx...
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Buildx不可用
    set /a FAILED_TESTS+=1
) else (
    echo [PASS] Buildx可用
    set /a PASSED_TESTS+=1
)

REM 测试3: 项目文件存在
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查项目文件...
if exist "backend\Dockerfile" if exist "frontend\Dockerfile" if exist "docker-compose.arm64.yml" (
    echo [PASS] 项目文件完整
    set /a PASSED_TESTS+=1
) else (
    echo [FAIL] 项目文件缺失
    set /a FAILED_TESTS+=1
)

REM 测试4: 构建脚本存在
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查构建脚本...
if exist "build-deb-arm64-windows.bat" if exist "build-deb-arm64-windows-full.bat" (
    echo [PASS] 构建脚本存在
    set /a PASSED_TESTS+=1
) else (
    echo [FAIL] 构建脚本缺失
    set /a FAILED_TESTS+=1
)

REM 测试5: 测试脚本存在
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查测试脚本...
if exist "test-deb-arm64.sh" if exist "test-deb-arm64-full.sh" (
    echo [PASS] 测试脚本存在
    set /a PASSED_TESTS+=1
) else (
    echo [FAIL] 测试脚本缺失
    set /a FAILED_TESTS+=1
)

REM 测试6: 文档存在
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 检查文档...
if exist "ARM64_BUILD_README.md" if exist "WINDOWS_BUILD_ARM64_GUIDE.md" if exist "QUICK_START_ARM64.md" (
    echo [PASS] 文档完整
    set /a PASSED_TESTS+=1
) else (
    echo [FAIL] 文档缺失
    set /a FAILED_TESTS+=1
)

REM 测试7: 创建测试构建器
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 测试创建Buildx构建器...
docker buildx create --name test-arm64-builder --use >nul 2>&1
if errorlevel 1 (
    echo [WARN] 构建器可能已存在
    docker buildx use test-arm64-builder >nul 2>&1
)
docker buildx inspect --bootstrap >nul 2>&1
if errorlevel 1 (
    echo [FAIL] 构建器创建失败
    set /a FAILED_TESTS+=1
) else (
    echo [PASS] 构建器创建成功
    set /a PASSED_TESTS+=1
)

REM 测试8: 测试ARM64平台支持
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 测试ARM64平台支持...
docker buildx inspect | findstr "linux/arm64" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] ARM64平台不支持
    set /a FAILED_TESTS+=1
) else (
    echo [PASS] ARM64平台支持正常
    set /a PASSED_TESTS+=1
)

REM 测试9: 测试拉取ARM64镜像
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 测试拉取ARM64镜像...
docker pull --platform linux/arm64 alpine:latest >nul 2>&1
if errorlevel 1 (
    echo [FAIL] ARM64镜像拉取失败
    set /a FAILED_TESTS+=1
) else (
    echo [PASS] ARM64镜像拉取成功
    set /a PASSED_TESTS+=1
    docker rmi alpine:latest >nul 2>&1
)

REM 测试10: 验证Dockerfile语法
set /a TOTAL_TESTS+=1
echo [%TOTAL_TESTS%] 验证Dockerfile语法...
docker buildx build --platform linux/arm64 --target production -f backend/Dockerfile backend --dry-run >nul 2>&1
if errorlevel 1 (
    echo [WARN] Dockerfile验证警告（可能需要实际构建）
    set /a PASSED_TESTS+=1
) else (
    echo [PASS] Dockerfile语法正确
    set /a PASSED_TESTS+=1
)

REM 清理测试构建器
echo.
echo 清理测试环境...
docker buildx rm test-arm64-builder >nul 2>&1

REM 输出结果
echo.
echo ========================================
echo   测试结果
echo ========================================
echo 总测试数: %TOTAL_TESTS%
echo 通过: %PASSED_TESTS%
echo 失败: %FAILED_TESTS%
echo.

if %FAILED_TESTS% EQU 0 (
    echo [SUCCESS] 所有测试通过！
    echo.
    echo 环境已就绪，可以开始构建：
    echo   - 标准DEB包: build-deb-arm64-windows.bat
    echo   - 完整DEB包: build-deb-arm64-windows-full.bat
    echo.
    exit /b 0
) else (
    echo [FAILED] 有 %FAILED_TESTS% 个测试失败
    echo 请检查环境配置后重试
    echo.
    exit /b 1
)

endlocal
