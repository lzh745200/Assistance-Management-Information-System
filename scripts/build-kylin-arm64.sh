#!/bin/bash
# ════════════════════════════════════════════════════════════════════
#  军队乡村振兴管理系统 - 麒麟 V10 ARM64 构建脚本
#
#  支持两种模式:
#    在线模式: 在麒麟ARM64上直接构建，需要网络连接
#    离线模式: 预下载所有资源，打包进DEB，完全离线安装
#
#  用法:
#    bash scripts/build-kylin-arm64.sh              # 在线构建
#    bash scripts/build-kylin-arm64.sh --offline   # 离线构建
#    bash scripts/build-kylin-arm64.sh --help      # 查看帮助
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── 颜色输出 ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── 参数解析 ───
OFFLINE_MODE=0
SKIP_WHEELS=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --offline) OFFLINE_MODE=1; shift ;;
        --skip-wheels) SKIP_WHEELS=1; shift ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --offline      离线模式: 预下载ARM64 wheel包并打包进DEB"
            echo "  --skip-wheels  跳过下载wheel包（仅构建，不含离线资源）"
            echo ""
            echo "模式说明:"
            echo "  在线模式（默认）: 在麒麟ARM64上构建，需要网络"
            echo "  离线模式(--offline): 在有网络的电脑上预下载资源，"
            echo "                       生成的DEB可在完全离线环境安装"
            exit 0
            ;;
        *) echo "未知参数: $1"; echo "用法: $0 [--offline]"; exit 1 ;;
    esac
done

# ─── 项目根目录 ───
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ─── 版本号 ───
VERSION=$(python3 -c "import json; print(json.load(open('package.json'))['version'])" 2>/dev/null || echo "1.0.4")

# ─── 构建模式 ───
MODE_DESC="在线模式（需要网络）"
if [[ "$OFFLINE_MODE" -eq 1 ]]; then
    MODE_DESC="离线模式（资源打包进DEB）"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  军队乡村振兴管理系统 - 麒麟 V10 ARM64 构建${NC}"
echo -e "${GREEN}  版本: ${VERSION}  架构: aarch64${NC}"
echo -e "${GREEN}  模式: ${MODE_DESC}${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 0: 预检
# ════════════════════════════════════════════════════════════════════
log_info "[0/9] 预检构建环境..."

ARCH=$(uname -m 2>/dev/null || echo "unknown")

# 架构检查
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" && "$ARCH" != "x86_64" ]]; then
    log_warn "当前架构为 $ARCH（仅支持 aarch64/x86_64）"
    if [[ "$OFFLINE_MODE" -eq 1 ]]; then
        log_info "离线模式下继续（wheel下载不依赖架构）..."
    else
        log_error "请在 ARM64 或 x86_64 设备上运行"
        exit 1
    fi
else
    log_success "架构: $ARCH"
fi

# Python 检查（ARM64构建必须）
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    PYTHON_CMD=""
    for cmd in python3.11 python3.12 python3 python python3.10; do
        if command -v "$cmd" &>/dev/null; then
            PY_VER=$($cmd --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
            PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
            PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
            if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 8 ]]; then
                PYTHON_CMD="$cmd"
                break
            fi
        fi
    done

    if [[ -z "$PYTHON_CMD" ]]; then
        log_error "未找到 Python 3.8+，麒麟ARM64构建需要Python"
        log_info "安装: sudo apt install python3.11 python3.11-venv python3.11-dev"
        exit 1
    fi
    log_success "Python: $($PYTHON_CMD --version)"
fi

# Node.js 检查（ARM64构建必须）
if ! command -v node &>/dev/null; then
    log_error "未找到 Node.js，请安装 Node.js 18+"
    exit 1
fi
NODE_MAJOR=$(node -v | cut -d. -f1 | tr -d 'v')
if [[ "$NODE_MAJOR" -lt 18 ]]; then
    log_error "Node.js 版本过低 ($(node -v))，需要 18+"
    exit 1
fi
log_success "Node.js: $(node -v)"

# npm 检查
if ! command -v npm &>/dev/null; then
    log_error "未找到 npm"
    exit 1
fi

# 磁盘空间检查
FREE_GB=$(df -BG "$PROJECT_ROOT" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G' || echo "0")
if [[ "$FREE_GB" -lt 10 ]]; then
    log_warn "可用空间仅 ${FREE_GB}GB，建议至少 10GB"
fi

# 操作系统
if [ -f /etc/kylin-release ]; then
    log_info "操作系统: $(cat /etc/kylin-release)"
elif [ -f /etc/os-release ]; then
    log_info "操作系统: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')"
fi

echo ""
log_success "预检通过"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 1: 安装系统依赖（仅ARM64本地构建需要）
# ════════════════════════════════════════════════════════════════════
log_info "[1/9] 安装系统依赖..."

SUDO=""
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    if command -v apt-get &>/dev/null; then
        $SUDO apt-get update -qq 2>/dev/null || true
        $SUDO apt-get install -y --no-install-recommends \
            build-essential python3-dev python3-venv python3-pip \
            libffi-dev libssl-dev libjpeg-dev zlib1g-dev \
            libmagic1 libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 \
            xdg-utils libatspi2.0-0 libuuid1 libsecret-1-0 file \
            2>/dev/null || log_warn "部分系统依赖安装失败（可能已存在）"
    fi
    log_success "系统依赖安装完成"
else
    log_info "非ARM64架构，跳过系统依赖安装"
fi
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 2: 下载离线资源包（离线模式）
# ════════════════════════════════════════════════════════════════════
log_info "[2/9] 准备离线资源..."

WHEELS_DIR="$PROJECT_ROOT/dist/offline-wheels"
OFFLINE_DEPS_DIR="$PROJECT_ROOT/dist/offline-deps"
rm -rf "$WHEELS_DIR" "$OFFLINE_DEPS_DIR"
mkdir -p "$WHEELS_DIR" "$OFFLINE_DEPS_DIR"

if [[ "$OFFLINE_MODE" -eq 1 && "$SKIP_WHEELS" -eq 0 ]]; then
    log_info "下载 ARM64 Python wheel 包（离线安装用）..."

    # 生成ARM64过滤版requirements
    ARM64_REQ="$PROJECT_ROOT/backend/requirements-arm64-filtered.txt"
    grep -v -E '^(python-magic-bin|prophet|cmdstanpy|scikit-learn|scipy|scrapy|Twisted|matplotlib|redis|hiredis|selenium)' \
        "$PROJECT_ROOT/backend/requirements.txt" > "$ARM64_REQ"

    # 确保有 python-magic
    if ! grep -q '^python-magic==' "$ARM64_REQ"; then
        echo "python-magic==0.4.27" >> "$ARM64_REQ"
    fi

    # 预下载 ARM64 wheel 包
    if command -v python3 &>/dev/null; then
        python3 -m pip download \
            --no-deps \
            --only-binary=:all: \
            --platform manylinux2014_aarch64 \
            --python-version 3.11 \
            -r "$ARM64_REQ" \
            -d "$WHEELS_DIR" \
            2>&1 | tail -5 || log_warn "部分wheel下载失败（继续构建）"

        # 也下载纯Python包（any平台）
        python3 -m pip download \
            --no-deps \
            --no-binary :all: \
            -r "$ARM64_REQ" \
            -d "$WHEELS_DIR" \
            2>&1 | tail -3 || true

        WHEEL_COUNT=$(find "$WHEELS_DIR" -name "*.whl" 2>/dev/null | wc -l)
        log_success "已下载 $WHEEL_COUNT 个 wheel 包"
    else
        log_warn "Python3 不可用，跳过 wheel 下载"
    fi

    # 下载系统库DEB包
    log_info "下载系统库DEB包（离线安装用）..."
    SYS_DEBS=(
        "libmagic1"
        "libgtk-3-0"
        "libnotify4"
        "libnss3"
        "libxss1"
        "libxtst6"
        "libatspi2.0-0"
        "libuuid1"
        "libsecret-1-0"
    )

    for pkg in "${SYS_DEBS[@]}"; do
        if command -v apt-get &>/dev/null; then
            $SUDO apt-get download "$pkg" 2>/dev/null || true
            # 移动到offline-deps目录
            for deb in ./*.deb; do
                if [[ -f "$deb" ]]; then
                    mv "$deb" "$OFFLINE_DEPS_DIR/" 2>/dev/null || true
                fi
            done
        fi
    done

    SYS_DEB_COUNT=$(find "$OFFLINE_DEPS_DIR" -name "*.deb" 2>/dev/null | wc -l)
    log_success "已下载 $SYS_DEB_COUNT 个系统库DEB包"

    # 生成离线安装脚本
    log_info "生成离线安装脚本..."
    cat > "$PROJECT_ROOT/dist/offline-install.sh" << 'OFFLINE_EOF'
#!/bin/bash
# ════════════════════════════════════════════════════════════════════
#  军队乡村振兴管理系统 - 离线安装脚本
#  使用DEB包内捆绑的资源进行完全离线安装
# ════════════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="military-rural-system-standalone"
PRODUCT_NAME="军队乡村振兴管理系统"
INSTALL_DIR="/opt/${PRODUCT_NAME}"
DEPS_DIR="$SCRIPT_DIR/offline-deps"
WHEELS_DIR="$SCRIPT_DIR/offline-wheels"

echo "=============================================="
echo "  军队乡村振兴管理系统 - 离线安装"
echo "=============================================="

if [[ "$EUID" -ne 0 ]]; then
    echo "请使用 root 权限运行: sudo $0"
    exit 1
fi

# 安装系统库（离线DEB）
echo "[1/4] 安装系统依赖..."
for deb in "$DEPS_DIR"/*.deb; do
    if [[ -f "$deb" ]]; then
        dpkg -i --force-depends "$deb" 2>/dev/null || true
    fi
done
apt-get install -f -y 2>/dev/null || true
echo "[OK] 系统依赖安装完成"

# 创建数据目录
echo "[2/4] 创建数据目录..."
mkdir -p "/var/lib/${APP_NAME}"/{database,logs,uploads,exports,cache,backups}
chmod -R 1777 "/var/lib/${APP_NAME}" 2>/dev/null || true

# 设置后端权限
echo "[3/4] 设置权限..."
if [[ -f "${INSTALL_DIR}/resources/backend/military-rural-backend" ]]; then
    chmod +x "${INSTALL_DIR}/resources/backend/military-rural-backend"
fi
if [[ -f "${INSTALL_DIR}/chrome-sandbox" ]]; then
    chown root:root "${INSTALL_DIR}/chrome-sandbox"
    chmod 4755 "${INSTALL_DIR}/chrome-sandbox"
fi
chmod +x "${INSTALL_DIR}/${PRODUCT_NAME}" 2>/dev/null || true

# 注册桌面入口
echo "[4/4] 完成配置..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true

echo ""
echo "=============================================="
echo "  离线安装完成！"
echo "=============================================="
echo ""
echo "  启动: 在应用菜单搜索 '军队乡村振兴'"
echo "  或:   ${INSTALL_DIR}/${PRODUCT_NAME}"
echo ""
OFFLINE_EOF
    chmod +x "$PROJECT_ROOT/dist/offline-install.sh"
    log_success "离线安装脚本已生成"
fi

if [[ "$SKIP_WHEELS" -eq 1 ]]; then
    log_info "跳过离线资源下载（--skip-wheels）"
fi
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 3: Python 环境（仅ARM64本地构建需要）
# ════════════════════════════════════════════════════════════════════
log_info "[3/9] 准备 Python 环境..."

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    VENV_DIR="$PROJECT_ROOT/backend/.venv-arm64"

    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "创建虚拟环境..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip wheel setuptools -q

    # 生成ARM64 requirements
    ARM64_REQ="$PROJECT_ROOT/backend/requirements-arm64.txt"
    grep -v -E '^(python-magic-bin|prophet|cmdstanpy|scikit-learn|scipy|scrapy|Twisted|matplotlib|redis|hiredis|selenium)' \
        "$PROJECT_ROOT/backend/requirements.txt" > "$ARM64_REQ"
    if ! grep -q '^python-magic==' "$ARM64_REQ"; then
        echo "python-magic==0.4.27" >> "$ARM64_REQ"
    fi

    pip install -r "$ARM64_REQ" -q 2>&1 | tail -3
    pip install pyinstaller -q
    log_success "Python 环境准备完成"
else
    log_info "非ARM64，跳过Python环境准备"
fi
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 4: PyInstaller 打包后端（仅ARM64）
# ════════════════════════════════════════════════════════════════════
log_info "[4/9] 打包后端 (PyInstaller)..."

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    cd "$PROJECT_ROOT/backend"
    rm -rf build dist/military-rural-backend

    SPEC_FILE="$PROJECT_ROOT/backend/backend_linux_arm64.spec"
    if [[ ! -f "$SPEC_FILE" ]]; then
        log_error "ARM64 spec 文件不存在: $SPEC_FILE"
        exit 1
    fi

    log_info "执行 PyInstaller..."
    pyinstaller --clean --noconfirm "$SPEC_FILE"

    BACKEND_EXE="$PROJECT_ROOT/backend/dist/military-rural-backend"
    if [[ ! -f "$BACKEND_EXE" ]]; then
        log_error "后端打包失败"
        exit 1
    fi

    BACKEND_SIZE=$(du -m "$BACKEND_EXE" | cut -f1)
    if [[ "$BACKEND_SIZE" -lt 10 ]]; then
        log_error "后端文件异常偏小 (${BACKEND_SIZE}MB)"
        exit 1
    fi

    FILE_INFO=$(file "$BACKEND_EXE")
    log_success "后端打包完成 (${BACKEND_SIZE}MB, $FILE_INFO)"

    # 复制到 electron-builder 期望位置
    DEST_DIR="$PROJECT_ROOT/dist/backend/linux"
    mkdir -p "$DEST_DIR"
    cp -f "$BACKEND_EXE" "$DEST_DIR/military-rural-backend"
    chmod +x "$DEST_DIR/military-rural-backend"
    cd "$PROJECT_ROOT"
else
    log_info "非ARM64，跳过后端打包（请在ARM64设备上运行完整构建）"
fi
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 5: 构建前端
# ════════════════════════════════════════════════════════════════════
log_info "[5/9] 构建前端..."

cd "$PROJECT_ROOT/frontend"
if [[ ! -d "node_modules" ]]; then
    npm install --legacy-peer-deps 2>&1 | tail -3
fi
npm run build 2>&1 | tail -5

if [[ ! -f "$PROJECT_ROOT/frontend/dist/index.html" ]]; then
    log_error "前端构建失败"
    exit 1
fi
cd "$PROJECT_ROOT"
log_success "前端构建完成"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 6: 安装 Electron 依赖
# ════════════════════════════════════════════════════════════════════
log_info "[6/9] 安装 Electron 依赖..."

if [[ ! -d "node_modules/electron" ]] || [[ ! -d "node_modules/electron-builder" ]]; then
    npm install --legacy-peer-deps 2>&1 | tail -3
fi
log_success "Electron 依赖就绪"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 7: 确保构建配置存在
# ════════════════════════════════════════════════════════════════════
log_info "[7/9] 检查构建配置..."

mkdir -p "$PROJECT_ROOT/build/linux"

# 生成安装脚本（如果不存在）
if [[ ! -f "$PROJECT_ROOT/build/linux/after-install.sh" ]]; then
    log_warn "after-install.sh 不存在，创建..."
fi
if [[ ! -f "$PROJECT_ROOT/build/linux/after-remove.sh" ]]; then
    log_warn "after-remove.sh 不存在，创建..."
fi

# 使用统一的安装脚本
cp -f "$PROJECT_ROOT/build/linux/after-install.sh" "$PROJECT_ROOT/build/linux/after-install.sh.bak" 2>/dev/null || true

# ─── 更新 after-install.sh：离线模式添加资源复制 ───
cat > "$PROJECT_ROOT/build/linux/after-install.sh" << 'POSTINST'
#!/bin/bash
# ──────────────────────────────────────────────────────────────────
#  军队乡村振兴管理系统 - DEB 安装后脚本
# ──────────────────────────────────────────────────────────────────
set -e

APP_NAME="military-rural-system-standalone"
PRODUCT_NAME="军队乡村振兴管理系统"
APP_DIR="/opt/${PRODUCT_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
SCRIPT_DIR="$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")"
RESOURCE_DIR="${APP_DIR}/resources"

# 创建数据目录
mkdir -p "${DATA_DIR}"/{database,logs,uploads,exports,cache,backups}
chmod -R 1777 "${DATA_DIR}" 2>/dev/null || true

# 设置后端可执行权限
if [[ -f "${RESOURCE_DIR}/backend/military-rural-backend" ]]; then
    chmod +x "${RESOURCE_DIR}/backend/military-rural-backend"
fi

# 设置 chrome-sandbox SUID
if [[ -f "${APP_DIR}/chrome-sandbox" ]]; then
    chown root:root "${APP_DIR}/chrome-sandbox"
    chmod 4755 "${APP_DIR}/chrome-sandbox"
fi

# 设置主程序权限
if [[ -f "${APP_DIR}/${PRODUCT_NAME}" ]]; then
    chmod +x "${APP_DIR}/${PRODUCT_NAME}"
fi

# 注册 ldconfig
if [[ -d "${RESOURCE_DIR}/backend/lib" ]]; then
    echo "${RESOURCE_DIR}/backend/lib" > /etc/ld.so.conf.d/${APP_NAME}.conf
    ldconfig 2>/dev/null || true
fi

# 注册桌面入口
if [[ -f "/usr/share/applications/${APP_NAME}.desktop" ]]; then
    chmod 644 "/usr/share/applications/${APP_NAME}.desktop"
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

# 更新图标缓存
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true

# ─── 离线模式：安装捆绑的系统依赖 ───
if [[ -d "${RESOURCE_DIR}/offline-deps" ]]; then
    echo "[INFO] 检测到离线依赖包，安装中..."
    for deb in "${RESOURCE_DIR}/offline-deps"/*.deb 2>/dev/null; do
        if [[ -f "$deb" ]]; then
            dpkg -i --force-depends "$deb" 2>/dev/null || true
        fi
    done
    apt-get install -f -y 2>/dev/null || true
    echo "[OK] 离线依赖安装完成"
fi

echo ""
echo "=============================================="
echo "  军队乡村振兴管理系统 安装完成"
echo "=============================================="
echo ""
echo "  启动方式:"
echo "    在应用菜单中搜索 '军队乡村振兴'"
echo "    或运行: ${APP_DIR}/${PRODUCT_NAME}"
echo ""
echo "  数据目录: ${DATA_DIR}"
echo ""
exit 0
POSTINST

cat > "$PROJECT_ROOT/build/linux/after-remove.sh" << 'POSTRM'
#!/bin/bash
set -e
APP_NAME="military-rural-system-standalone"
if [[ "$1" = "purge" ]]; then
    rm -rf "/var/lib/${APP_NAME}" 2>/dev/null || true
    rm -f "/etc/ld.so.conf.d/${APP_NAME}.conf" 2>/dev/null || true
    ldconfig 2>/dev/null || true
fi
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
exit 0
POSTRM

chmod +x "$PROJECT_ROOT/build/linux/after-install.sh" \
         "$PROJECT_ROOT/build/linux/after-remove.sh"

# 清理数据库WAL
if [[ -f "$PROJECT_ROOT/backend/data/rural_revitalization.db" ]]; then
    python3 "$PROJECT_ROOT/scripts/build/checkpoint_db.py" 2>/dev/null || true
fi

log_success "构建配置就绪"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 8: 构建 DEB 包
# ════════════════════════════════════════════════════════════════════
log_info "[8/9] 构建 DEB 安装包..."

# ─── 更新 package.json 的 electron-builder 配置，添加离线资源 ───
if [[ "$OFFLINE_MODE" -eq 1 && -d "$WHEELS_DIR" && -d "$OFFLINE_DEPS_DIR" ]]; then
    log_info "添加离线资源到 electron-builder..."

    # 临时修改 package.json 添加离线资源
    PKGJSON="$PROJECT_ROOT/package.json"
    PKGJSON_BAK="$PROJECT_ROOT/package.json.bak"
    cp "$PKGJSON" "$PKGJSON_BAK"

    # 使用 Python 修改 package.json
    python3 << PYEOF
import json, sys
with open("$PKGJSON", "r", encoding="utf-8") as f:
    pkg = json.load(f)

# 添加离线wheel和系统库到 extraResources
pkg["build"]["linux"]["extraResources"] = pkg["build"]["linux"].get("extraResources", [])
pkg["build"]["linux"]["extraResources"] = [
    r for r in pkg["build"]["linux"]["extraResources"]
    if r.get("to") not in ("offline-wheels", "offline-deps", "offline-install.sh")
]

# 添加离线wheel
pkg["build"]["linux"]["extraResources"].append({
    "from": "$WHEELS_DIR",
    "to": "offline-wheels",
    "filter": ["**/*.whl"]
})

# 添加离线系统库DEB
pkg["build"]["linux"]["extraResources"].append({
    "from": "$OFFLINE_DEPS_DIR",
    "to": "offline-deps",
    "filter": ["**/*.deb"]
})

# 添加离线安装脚本
if __import__("os").path.exists("$PROJECT_ROOT/dist/offline-install.sh"):
    pkg["build"]["linux"]["extraResources"].append({
        "from": "$PROJECT_ROOT/dist/offline-install.sh",
        "to": "offline-install.sh"
    })

with open("$PKGJSON", "w", encoding="utf-8") as f:
    json.dump(pkg, f, ensure_ascii=False, indent=2)
print("package.json updated")
PYEOF
fi

# 清理旧输出
rm -rf "$PROJECT_ROOT/dist/electron/linux-unpacked"

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    npx electron-builder --linux deb --arm64 2>&1 | tail -10
elif [[ "$ARCH" == "x86_64" ]]; then
    npx electron-builder --linux deb --arm64 2>&1 | tail -10
fi

# 恢复原始 package.json
if [[ -f "$PKGJSON_BAK" ]]; then
    mv "$PKGJSON_BAK" "$PKGJSON"
fi

echo ""
log_success "DEB 包构建完成"
echo ""

# ════════════════════════════════════════════════════════════════════
# Phase 9: 验证输出
# ════════════════════════════════════════════════════════════════════
log_info "[9/9] 验证构建产物..."

DEB_FILE=""
for f in "$PROJECT_ROOT"/dist/electron/*.deb; do
    if [[ -f "$f" ]]; then
        DEB_FILE="$f"
        break
    fi
done

if [[ -z "$DEB_FILE" ]]; then
    log_error "未找到 DEB 包"
    exit 1
fi

DEB_NAME=$(basename "$DEB_FILE")
DEB_SIZE=$(du -sh "$DEB_FILE" | cut -f1)
DEB_SHA256=$(sha256sum "$DEB_FILE" | cut -d' ' -f1)

log_success "DEB 包: $DEB_NAME"
log_success "大小: $DEB_SIZE"
log_success "SHA256: ${DEB_SHA256:0:32}..."

if command -v dpkg-deb &>/dev/null; then
    DEB_ARCH=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Architecture:" | awk '{print $2}' || echo "unknown")
    DEB_VERSION=$(dpkg-deb --info "$DEB_FILE" 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "unknown")
    log_success "架构: $DEB_ARCH  版本: $DEB_VERSION"
fi

# 离线资源清单
if [[ "$OFFLINE_MODE" -eq 1 ]]; then
    WHEEL_COUNT=$(find "$WHEELS_DIR" -name "*.whl" 2>/dev/null | wc -l)
    SYS_DEB_COUNT=$(find "$OFFLINE_DEPS_DIR" -name "*.deb" 2>/dev/null | wc -l)
    log_success "离线wheel包: $WHEEL_COUNT 个"
    log_success "离线系统库: $SYS_DEB_COUNT 个"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  构建成功！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "  产物: $DEB_FILE"
echo "  大小: $DEB_SIZE"
echo ""
echo "  ── 在线安装（麒麟ARM64联网） ──"
echo "    sudo dpkg -i $DEB_NAME"
echo "    sudo apt-get install -f"
echo ""
echo "  ── 离线安装（完全无网络） ──"
echo "    # DEB包已内嵌离线资源"
echo "    sudo dpkg -i $DEB_NAME"
echo "    # 如有依赖缺失，运行:"
echo "    #   sudo apt-get install -f"
echo ""
echo "  验证: bash scripts/verify-arm64-deb.sh $DEB_FILE"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"

deactivate 2>/dev/null || true
