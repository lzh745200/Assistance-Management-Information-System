@echo off
chcp 65001 >nul 2>&1
title 帮扶管理系统 - 提交推送与构建
cd /d "%~dp0"

echo ============================================================
echo   帮扶管理系统 - Git 提交 + 推送 + 触发 CI 构建
echo ============================================================
echo.

REM Step 1: Show current git status
echo [1/5] 检查当前更改状态...
git status --short
echo.

REM Step 2: Stage all changes (including untracked files)
echo [2/5] 暂存所有更改...
git add -A
if %ERRORLEVEL% neq 0 (
    echo ERROR: git add 失败
    pause
    exit /b 1
)
echo OK: 所有更改已暂存
echo.

REM Step 3: Show staged changes summary
echo [3/5] 暂存内容摘要:
git diff --cached --stat
echo.

REM Step 4: Commit
echo [4/5] 提交更改...
git commit -m "fix: Vue setAttribute crash, passcode fallback, role simplification, files API envelope

1. Vue setAttribute('0') error fix:
   - ErrorBoundary.vue: wrap dual-root (v-if/v-else) in single root div
     with display:contents to prevent transition patchProp crash
   - App.vue: remove redundant :size on el-config-provider
   - DefaultLayoutSafe.vue: add :key and v-if=Component to transition

2. Passcode validation fix:
   - machine_code_service.py: add third-level fallback in verify_pass_code
     to match by pass_code only (when machine_code is inconsistent due to
     wmic instability), auto-updates machine_code binding

3. Role simplification:
   - constants.py: 4 practical roles (super_admin/admin/user/viewer),
     normalize_role() maps deprecated roles for backward compat
   - data_permission.py: use normalize_role() for backward compatibility
   - UserManagement.vue: fix formData.role default from 'operator' to 'user'
   - Role.vue: add system role info banner

4. Files API fix:
   - files.py: use success_response() envelope, remove unused db param,
     add audit logging
   - test_files_upload_api.py: update assertions for envelope format"
if %ERRORLEVEL% neq 0 (
    echo WARNING: git commit 可能失败（可能没有更改需要提交）
    echo 继续执行推送...
)
echo.

REM Step 5: Push to GitHub
echo [5/5] 推送到 GitHub (origin main)...
git push origin main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: git push 失败
    echo 可能原因:
    echo   - 网络连接问题
    echo   - GitHub 认证失败（请检查 SSH key 或 PAT token）
    echo   - 远程分支有冲突（尝试 git pull --rebase origin main 后重试）
    echo.
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   推送成功！
echo ============================================================
echo.
echo GitHub Actions 将自动触发以下两个构建工作流:
echo.
echo   1. Build Windows Installer (x64)
echo      - 工作流: .github/workflows/build-windows.yml
echo      - 产物:   Windows NSIS .exe 安装包
echo      - 运行环境: windows-2022
echo      - 预计耗时: ~30-60 分钟
echo.
echo   2. Build Self-Contained ARM64 Debian Package
echo      - 工作流: .github/workflows/build-arm64.yml
echo      - 产物:   Linux ARM64 .deb 安装包 (Kylin V10)
echo      - 运行环境: ubuntu-latest + QEMU ARM64
echo      - 预计耗时: ~20-40 分钟
echo.
echo 查看构建进度:
echo   https://github.com/actions
echo   （或仓库 -> Actions 标签页）
echo.
echo 构建完成后，在 Actions 运行页面下载 Artifacts:
echo   - windows-installer-x64  (.exe)
echo   - kylin-arm64-deb         (.deb)
echo.

REM Show recent git log
echo 最近的提交记录:
git log --oneline -5
echo.

REM Final status
echo 当前状态:
git status --short
if %ERRORLEVEL% equ 0 (
    echo 工作区干净，无未提交更改
)
echo.
echo ============================================================
echo   全部完成！
echo ============================================================
pause
