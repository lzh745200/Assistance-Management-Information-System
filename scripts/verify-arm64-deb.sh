#!/bin/bash
# ══════════════════════════════════════════════════════════
#  军队乡村振兴管理系统 - ARM64 DEB 包全面验证脚本
#  在麒麟 V10 ARM64 上运行，验证 DEB 包的完整性和功能
#
#  用法:
#    bash scripts/verify-arm64-deb.sh [deb文件路径]
#    bash scripts/verify-arm64-deb.sh dist/electron/military-rural-system_1.0.4_arm64.deb
# ══════════════════════════════════════════════════════════
set -euo pipefail

# ─── 颜色输出 ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() { ((PASS++)); echo -e "  ${GREEN}[PASS]${NC} $1"; }
check_fail() { ((FAIL++)); echo -e "  ${RED}[FAIL]${NC} $1"; }
check_warn() { ((WARN++)); echo -e "  ${YELLOW}[WARN]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── 确定 DEB 文件 ───
if [[ $# -ge 1 ]]; then
    DEB_FILE="$1"
else
    VERSION=$(python3 -c "import json; print(json.load(open('${PROJECT_ROOT}/package.json'))['version'])" 2>/dev/null || echo "1.0.4")
    DEB_FILE="${PROJECT_ROOT}/dist/electron/military-rural-system_${VERSION}_arm64.deb"
fi

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ARM64 DEB 包验证${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  DEB: $DEB_FILE"
echo ""

# ══════════════════════════════════════════════════════════
# Test 1: 文件存在性
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[1/8] 文件存在性检查${NC}"

if [[ -f "$DEB_FILE" ]]; then
    check_pass "DEB 文件存在"
else
    check_fail "DEB 文件不存在: $DEB_FILE"
    echo ""
    echo -e "${RED}验证终止：DEB 文件不存在${NC}"
    exit 1
fi

DEB_SIZE=$(du -sh "$DEB_FILE" | cut -f1)
DEB_SIZE_BYTES=$(stat -c %s "$DEB_FILE" 2>/dev/null || stat -f %z "$DEB_FILE" 2>/dev/null || echo 0)

if [[ "$DEB_SIZE_BYTES" -gt 104857600 ]]; then
    check_pass "文件大小正常: $DEB_SIZE (> 100MB)"
elif [[ "$DEB_SIZE_BYTES" -gt 52428800 ]]; then
    check_warn "文件大小偏小: $DEB_SIZE (< 100MB)"
else
    check_fail "文件大小异常: $DEB_SIZE (< 50MB)"
fi

SHA256=$(sha256sum "$DEB_FILE" | cut -d' ' -f1)
echo -e "  SHA256: ${SHA256:0:32}..."
echo ""

# ══════════════════════════════════════════════════════════
# Test 2: DEB 元数据验证
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[2/8] DEB 元数据验证${NC}"

if command -v dpkg-deb &>/dev/null; then
    # 获取元数据
    DEB_INFO=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null || echo "")

    if [[ -n "$DEB_INFO" ]]; then
        check_pass "dpkg-deb --info 成功"

        # 检查架构
        DEB_ARCH=$(echo "$DEB_INFO" | grep "Architecture:" | awk '{print $2}')
        if [[ "$DEB_ARCH" == "arm64" ]]; then
            check_pass "架构: $DEB_ARCH"
        else
            check_fail "架构不正确: $DEB_ARCH (期望 arm64)"
        fi

        # 检查包名
        DEB_PKG=$(echo "$DEB_INFO" | grep "Package:" | awk '{print $2}')
        if [[ "$DEB_PKG" == "military-rural-system-standalone" ]]; then
            check_pass "包名: $DEB_PKG"
        else
            check_warn "包名: $DEB_PKG (期望 military-rural-system-standalone)"
        fi

        # 检查版本
        DEB_VER=$(echo "$DEB_INFO" | grep "Version:" | awk '{print $2}')
        if [[ -n "$DEB_VER" ]]; then
            check_pass "版本: $DEB_VER"
        else
            check_warn "无法读取版本号"
        fi

        # 检查依赖
        DEB_DEPS=$(echo "$DEB_INFO" | grep "Depends:" || echo "")
        REQUIRED_DEPS="libgtk-3-0 libnss3 libmagic1 libxtst6"
        for dep in $REQUIRED_DEPS; do
            if echo "$DEB_DEPS" | grep -q "$dep"; then
                check_pass "依赖 $dep 已声明"
            else
                check_warn "依赖 $dep 未在 DEB 中声明"
            fi
        done
    else
        check_fail "dpkg-deb --info 失败"
    fi
else
    check_warn "dpkg-deb 不可用，跳过元数据验证"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 3: 文件结构验证
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[3/8] 文件结构验证${NC}"

if command -v dpkg-deb &>/dev/null; then
    CONTENTS=$(dpkg-deb --contents "$DEB_FILE" 2>/dev/null || echo "")

    # 检查关键文件
    CHECK_FILES=(
        "opt/"
        "control.tar.gz"
        "data.tar"
    )

    for pattern in "opt/军队乡村振兴管理系统/" "usr/share/applications/" "usr/share/icons/"; do
        if echo "$CONTENTS" | grep -q "$pattern" 2>/dev/null; then
            check_pass "包含: $pattern"
        else
            check_warn "缺少: $pattern"
        fi
    done

    # 检查后端可执行文件
    if echo "$CONTENTS" | grep -q "military-rural-backend" 2>/dev/null; then
        check_pass "包含后端可执行文件"
    else
        check_fail "缺少后端可执行文件"
    fi

    # 检查 Electron 二进制
    if echo "$CONTENTS" | grep -q "chrome-sandbox\|electron\|军队乡村振兴管理系统" 2>/dev/null; then
        check_pass "包含 Electron 资源"
    else
        check_warn "未检测到 Electron 资源"
    fi

    # 检查前端文件
    if echo "$CONTENTS" | grep -q "index.html" 2>/dev/null; then
        check_pass "包含前端 index.html"
    else
        check_warn "缺少前端 index.html"
    fi
else
    check_warn "dpkg-deb 不可用，跳过文件结构验证"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 4: 安装测试
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[4/8] 安装测试${NC}"

# 检查是否有 root 权限
if [[ "$EUID" -eq 0 ]]; then
    # 执行安装
    if dpkg -i "$DEB_FILE" 2>&1; then
        check_pass "dpkg -i 安装成功"
    else
        # 尝试修复依赖
        apt-get install -f -y 2>&1 | tail -3
        if dpkg -i "$DEB_FILE" 2>&1; then
            check_pass "修复依赖后安装成功"
        else
            check_fail "安装失败"
        fi
    fi

    # 检查安装后的文件
    APP_DIR="/opt/军队乡村振兴管理系统"
    if [[ -d "$APP_DIR" ]]; then
        check_pass "安装目录存在: $APP_DIR"
    else
        check_fail "安装目录不存在: $APP_DIR"
    fi

    # 检查后端可执行文件
    BACKEND_EXE="${APP_DIR}/resources/backend/military-rural-backend"
    if [[ -f "$BACKEND_EXE" ]]; then
        check_pass "后端可执行文件存在"

        # 验证 ELF 架构
        FILE_INFO=$(file "$BACKEND_EXE")
        if echo "$FILE_INFO" | grep -q "aarch64\|ARM"; then
            check_pass "后端 ELF 架构: ARM aarch64"
        else
            check_fail "后端 ELF 架构不正确: $FILE_INFO"
        fi

        # 验证可执行权限
        if [[ -x "$BACKEND_EXE" ]]; then
            check_pass "后端有可执行权限"
        else
            check_fail "后端无可执行权限"
        fi
    else
        check_fail "后端可执行文件不存在: $BACKEND_EXE"
    fi

    # 检查 Electron 主程序
    if [[ -x "${APP_DIR}/军队乡村振兴管理系统" ]]; then
        check_pass "Electron 主程序有可执行权限"
    else
        check_warn "Electron 主程序可能缺少可执行权限"
    fi

    # 检查 chrome-sandbox
    if [[ -f "${APP_DIR}/chrome-sandbox" ]]; then
        SANDBOX_PERMS=$(stat -c %a "${APP_DIR}/chrome-sandbox" 2>/dev/null || echo "000")
        if [[ "$SANDBOX_PERMS" == "4755" ]]; then
            check_pass "chrome-sandbox 权限正确 (4755)"
        else
            check_warn "chrome-sandbox 权限: $SANDBOX_PERMS (期望 4755)"
        fi
    fi

    # 检查桌面入口
    DESKTOP_FILE="/usr/share/applications/military-rural-system-standalone.desktop"
    if [[ -f "$DESKTOP_FILE" ]]; then
        check_pass "桌面入口文件存在"
    else
        check_warn "桌面入口文件不存在"
    fi

else
    check_warn "非 root 用户，跳过安装测试"
    check_warn "使用 sudo 运行此脚本可执行安装测试"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 5: 后端健康检查
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[5/8] 后端健康检查${NC}"

BACKEND_PID=""
BACKEND_PORT=8000

# 查找后端可执行文件
BACKEND_CANDIDATES=(
    "/opt/军队乡村振兴管理系统/resources/backend/military-rural-backend"
    "${PROJECT_ROOT}/dist/backend/linux/military-rural-backend"
)

BACKEND_EXE_PATH=""
for candidate in "${BACKEND_CANDIDATES[@]}"; do
    if [[ -f "$candidate" && -x "$candidate" ]]; then
        BACKEND_EXE_PATH="$candidate"
        break
    fi
done

if [[ -n "$BACKEND_EXE_PATH" ]]; then
    log_info "启动后端: $BACKEND_EXE_PATH"

    # 设置临时数据库
    TEMP_DB_DIR=$(mktemp -d)
    export DATABASE_URL="sqlite:///${TEMP_DB_DIR}/test.db"
    export HOST="127.0.0.1"
    export PORT="$BACKEND_PORT"
    export SECRET_KEY="test-secret-key-for-verification-only"
    export CSRF_SECRET_KEY="test-csrf-key"

    "$BACKEND_EXE_PATH" &
    BACKEND_PID=$!

    # 等待后端启动
    READY=false
    for i in $(seq 1 60); do
        if curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null 2>&1; then
            READY=true
            break
        fi
        sleep 0.5
    done

    if [[ "$READY" == "true" ]]; then
        check_pass "后端启动成功 (PID: $BACKEND_PID)"

        # 详细健康检查
        HEALTH=$(curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" 2>/dev/null || echo "{}")
        if echo "$HEALTH" | grep -q "ok\|healthy\|200" 2>/dev/null; then
            check_pass "健康检查端点返回正常"
        else
            check_warn "健康检查返回: $HEALTH"
        fi
    else
        check_fail "后端启动超时 (60s)"
    fi
else
    check_warn "后端可执行文件不可用，跳过健康检查"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 6: 前端可访问性
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[6/8] 前端可访问性${NC}"

if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    FRONTEND_HTML=$(curl -sf "http://127.0.0.1:${BACKEND_PORT}/" 2>/dev/null || echo "")

    if [[ -n "$FRONTEND_HTML" ]] && echo "$FRONTEND_HTML" | grep -q "html" 2>/dev/null; then
        check_pass "前端页面可访问"
    else
        check_warn "前端页面不可访问（可能需要手动验证）"
    fi

    # 检查 API 文档
    DOCS_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}/docs" 2>/dev/null || echo "000")
    if [[ "$DOCS_STATUS" == "200" ]]; then
        check_pass "API 文档可访问 (/docs)"
    else
        check_warn "API 文档状态: $DOCS_STATUS"
    fi
else
    check_warn "后端未运行，跳过前端测试"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 7: 数据库初始化
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[7/8] 数据库初始化检查${NC}"

if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    # 检查临时数据库是否创建
    if [[ -f "${TEMP_DB_DIR}/test.db" ]]; then
        DB_SIZE=$(du -h "${TEMP_DB_DIR}/test.db" | cut -f1)
        check_pass "数据库文件已创建 (${DB_SIZE})"
    else
        check_warn "数据库文件未在预期位置创建"
    fi

    # 检查系统健康 API
    SYS_HEALTH=$(curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/system/health" 2>/dev/null || echo "")
    if echo "$SYS_HEALTH" | grep -q "database\|connected\|ok" 2>/dev/null; then
        check_pass "系统健康 API 返回数据库连接正常"
    else
        check_warn "系统健康 API 返回: $(echo "$SYS_HEALTH" | head -c 100)"
    fi
else
    check_warn "后端未运行，跳过数据库测试"
fi

echo ""

# ══════════════════════════════════════════════════════════
# Test 8: 库依赖完整性
# ══════════════════════════════════════════════════════════
echo -e "${CYAN}[8/8] 库依赖完整性${NC}"

if command -v ldd &>/dev/null; then
    for candidate in "${BACKEND_CANDIDATES[@]}"; do
        if [[ -f "$candidate" ]]; then
            MISSING=$(ldd "$candidate" 2>/dev/null | grep "not found" || echo "")
            if [[ -z "$MISSING" ]]; then
                check_pass "后端库依赖完整: $candidate"
            else
                check_fail "后端缺少库依赖:"
                echo "$MISSING" | while read -r line; do
                    echo -e "    ${RED}$line${NC}"
                done
            fi
            break
        fi
    done

    # 检查 Electron 二进制
    ELECTRON_BIN="/opt/军队乡村振兴管理系统/军队乡村振兴管理系统"
    if [[ -f "$ELECTRON_BIN" ]]; then
        E_MISSING=$(ldd "$ELECTRON_BIN" 2>/dev/null | grep "not found" || echo "")
        if [[ -z "$E_MISSING" ]]; then
            check_pass "Electron 库依赖完整"
        else
            check_fail "Electron 缺少库依赖:"
            echo "$E_MISSING" | while read -r line; do
                echo -e "    ${RED}$line${NC}"
            done
        fi
    fi
else
    check_warn "ldd 不可用，跳过库依赖检查"
fi

echo ""

# ─── 清理 ───
if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
fi

if [[ -d "$TEMP_DB_DIR" ]]; then
    rm -rf "$TEMP_DB_DIR"
fi

# ─── 汇总报告 ───
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  验证报告${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}PASS${NC}: $PASS"
echo -e "  ${YELLOW}WARN${NC}: $WARN"
echo -e "  ${RED}FAIL${NC}: $FAIL"
echo ""

if [[ "$FAIL" -eq 0 ]]; then
    echo -e "${GREEN}  所有测试通过！DEB 包可以正常使用${NC}"
    echo ""
    echo "  安装命令:"
    echo "    sudo dpkg -i $(basename "$DEB_FILE")"
    echo "    sudo apt-get install -f"
    echo ""
    exit 0
else
    echo -e "${RED}  有 $FAIL 项测试失败，请检查上方输出${NC}"
    exit 1
fi
