#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  军队乡村振兴管理系统 - 麒麟 V10 ARM64 DEB 包验证脚本
#  用法: bash scripts/verify-kylin-deb.sh [deb_file]
# ═══════════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }
info() { echo -e "  ${CYAN}[INFO]${NC} $1"; }

# ── 参数解析 ──
DEB_FILE="${1:-dist/deb/kylin/military-rural-system_1.1.0_arm64.deb}"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  麒麟 V10 ARM64 DEB 包验证${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# ══════════════════════════════════════════════════════════════
# 1. 文件存在性检查
# ══════════════════════════════════════════════════════════════
echo "1. 文件存在性检查"

if [ ! -f "$DEB_FILE" ]; then
    fail "DEB 文件不存在: $DEB_FILE"
    echo ""
    echo "请先构建: make build-kylin-arm64"
    exit 1
fi
pass "DEB 文件存在: $(basename $DEB_FILE)"

# 文件大小检查
DEB_SIZE=$(stat -c%s "$DEB_FILE" 2>/dev/null || stat -f%z "$DEB_FILE" 2>/dev/null)
DEB_SIZE_MB=$((DEB_SIZE / 1024 / 1024))

if [ "$DEB_SIZE_MB" -lt 30 ]; then
    fail "DEB 文件过小 (${DEB_SIZE_MB}MB)，可能构建不完整"
elif [ "$DEB_SIZE_MB" -gt 200 ]; then
    warn "DEB 文件较大 (${DEB_SIZE_MB}MB)，可能包含了不必要的依赖"
else
    pass "DEB 文件大小合理: ${DEB_SIZE_MB}MB"
fi

# ══════════════════════════════════════════════════════════════
# 2. DEB 包元数据检查
# ══════════════════════════════════════════════════════════════
echo ""
echo "2. DEB 包元数据检查"

if command -v dpkg-deb &>/dev/null; then
    # 架构检查
    DEB_ARCH=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Architecture:" | awk '{print $2}')
    if [ "$DEB_ARCH" = "arm64" ]; then
        pass "架构正确: $DEB_ARCH"
    else
        fail "架构错误: $DEB_ARCH (应为 arm64)"
    fi

    # 版本号
    DEB_VER=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Version:" | awk '{print $2}')
    info "版本号: $DEB_VER"

    # 包名
    DEB_PKG=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Package:" | awk '{print $2}')
    info "包名: $DEB_PKG"

    # 依赖
    DEB_DEPS=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Depends:" | head -1)
    info "依赖: $DEB_DEPS"
else
    warn "dpkg-deb 不可用，跳过元数据检查"
fi

# ══════════════════════════════════════════════════════════════
# 3. DEB 包内容检查
# ══════════════════════════════════════════════════════════════
echo ""
echo "3. DEB 包内容检查"

# 列出包内文件
CONTENTS=$(dpkg-deb --contents "$DEB_FILE" 2>/dev/null || true)

# 后端二进制
if echo "$CONTENTS" | grep -q "military-rural-backend"; then
    pass "后端可执行文件存在"
else
    fail "后端可执行文件缺失"
fi

# 前端文件
if echo "$CONTENTS" | grep -q "index.html"; then
    pass "前端 index.html 存在"
else
    fail "前端 index.html 缺失"
fi

# systemd 服务
if echo "$CONTENTS" | grep -q "military-rural.service"; then
    pass "systemd 服务文件存在"
else
    fail "systemd 服务文件缺失"
fi

# 启动脚本
if echo "$CONTENTS" | grep -q "start-kylin.sh"; then
    pass "启动脚本存在"
else
    fail "启动脚本缺失"
fi

# 桌面快捷方式
if echo "$CONTENTS" | grep -q "military-rural-system.desktop"; then
    pass "桌面快捷方式存在"
else
    fail "桌面快捷方式缺失"
fi

# 配置文件
if echo "$CONTENTS" | grep -q "kylin.env"; then
    pass "麒麟配置文件存在"
else
    fail "麒麟配置文件缺失"
fi

# DEBIAN 控制脚本
if echo "$CONTENTS" | grep -q "postinst"; then
    pass "安装后脚本 (postinst) 存在"
else
    fail "安装后脚本 (postinst) 缺失"
fi

if echo "$CONTENTS" | grep -q "prerm"; then
    pass "卸载前脚本 (prerm) 存在"
else
    fail "卸载前脚本 (prerm) 缺失"
fi

if echo "$CONTENTS" | grep -q "postrm"; then
    pass "卸载后脚本 (postrm) 存在"
else
    fail "卸载后脚本 (postrm) 缺失"
fi

# 不应包含 Electron 相关文件
if echo "$CONTENTS" | grep -qi "electron"; then
    fail "DEB 包中包含 Electron 相关文件（应为无 Electron 版本）"
else
    pass "不包含 Electron（符合一体化单机版要求）"
fi

if echo "$CONTENTS" | grep -qi "chrome-sandbox"; then
    fail "DEB 包中包含 chrome-sandbox（不应有 Chromium 组件）"
else
    pass "不包含 Chromium 组件"
fi

# ══════════════════════════════════════════════════════════════
# 4. SHA256 校验和
# ══════════════════════════════════════════════════════════════
echo ""
echo "4. 校验和"

if command -v sha256sum &>/dev/null; then
    SHA256=$(sha256sum "$DEB_FILE" | cut -d' ' -f1)
    info "SHA256: $SHA256"
elif command -v shasum &>/dev/null; then
    SHA256=$(shasum -a 256 "$DEB_FILE" | cut -d' ' -f1)
    info "SHA256: $SHA256"
else
    warn "sha256sum/shasum 不可用，跳过校验和"
fi

# ══════════════════════════════════════════════════════════════
# 5. 部署文件完整性检查（源码目录）
# ══════════════════════════════════════════════════════════════
echo ""
echo "5. 源码部署文件完整性"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

check_file() {
    if [ -f "$PROJECT_ROOT/$1" ]; then
        pass "$1"
    else
        fail "$1 不存在"
    fi
}

check_file "deploy/kylin/systemd/military-rural.service"
check_file "deploy/kylin/config/kylin.env"
check_file "deploy/kylin/scripts/start-kylin.sh"
check_file "deploy/kylin/desktop/military-rural-system.desktop"
check_file "deploy/kylin/DEBIAN/postinst"
check_file "deploy/kylin/DEBIAN/prerm"
check_file "deploy/kylin/DEBIAN/postrm"
check_file "docker/Dockerfile.kylin-standalone"
check_file "backend/backend_linux_arm64_standalone.spec"

# ══════════════════════════════════════════════════════════════
# 验证报告
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}  验证通过！${NC}"
    echo -e "${GREEN}  PASS: $PASS  WARN: $WARN  FAIL: $FAIL${NC}"
else
    echo -e "${RED}  验证失败！${NC}"
    echo -e "${RED}  PASS: $PASS  WARN: $WARN  FAIL: $FAIL${NC}"
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "安装方法:"
    echo "  sudo dpkg -i $(basename $DEB_FILE)"
    echo "  sudo apt-get install -f"
    echo ""
    echo "启动方法:"
    echo "  military-rural-system"
    echo "  或: sudo systemctl start military-rural-system"
    echo ""
fi

exit $FAIL
