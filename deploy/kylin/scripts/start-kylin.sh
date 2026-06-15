#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  帮扶管理信息系统 - 麒麟 V10 桌面启动入口
#  由 .desktop 文件调用，负责启动服务并打开浏览器
# ═══════════════════════════════════════════════════════════════
set -e

APP_NAME="assistance-management-system"
SERVICE_NAME="${APP_NAME}.service"
HEALTH_URL="http://127.0.0.1:8000/health"
BROWSER_URL="http://127.0.0.1:8000"
MAX_WAIT=60  # 最大等待秒数（首次启动数据库初始化可能较慢）

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[启动]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
err()  { echo -e "${RED}[错误]${NC} $1"; }

# ── 1. 启动 systemd 服务 ──
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    log "后端服务已在运行"
else
    log "正在启动后端服务..."
    if command -v pkexec &>/dev/null; then
        pkexec systemctl start "$SERVICE_NAME" 2>/dev/null || {
            warn "pkexec 不可用，尝试 sudo..."
            sudo systemctl start "$SERVICE_NAME" 2>/dev/null || {
                err "无法启动服务。请手动运行:"
                err "  sudo systemctl start $APP_NAME"
                # 尝试直接启动（非 systemd 模式）
                warn "尝试直接启动后端..."
                _direct_start &
            }
        }
    else
        sudo systemctl start "$SERVICE_NAME" 2>/dev/null || {
            warn "无法启动 systemd 服务，尝试直接启动..."
            _direct_start &
        }
    fi
fi

# ── 直接启动回退函数 ──
_direct_start() {
    if [ -x /opt/assistance-management-system/backend/assistance-management-backend ]; then
        cd /opt/assistance-management-system
        export KYLIN_MODE=true
        export FRONTEND_DIST_PATH=/opt/assistance-management-system/frontend
        export DATABASE_URL=sqlite:////var/lib/assistance-management-system/database/rural_revitalization.db
        export UPLOAD_DIR=/var/lib/assistance-management-system/uploads
        export EXPORT_DIR=/var/lib/assistance-management-system/exports
        export CACHE_DIR=/var/lib/assistance-management-system/cache
        export BACKUP_DIR=/var/lib/assistance-management-system/backups
        export LOG_DIR=/var/log/assistance-management-system
        export LOG_FILE=/var/log/assistance-management-system/app.log
        export HOST=127.0.0.1
        export PORT=8000
        /opt/assistance-management-system/backend/assistance-management-backend
    else
        err "后端可执行文件不存在"
        err "请重新安装: sudo dpkg -i assistance-management-system_*.deb"
    fi
}

# ── 2. 等待服务就绪 ──
log "等待服务就绪..."
for i in $(seq 1 $MAX_WAIT); do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        log "服务已就绪（耗时 ${i}s）"
        break
    fi
    if [ "$i" -eq "$MAX_WAIT" ]; then
        err "服务启动超时（${MAX_WAIT}s），请检查日志:"
        err "  sudo journalctl -u $APP_NAME -n 50 --no-pager"
        err "  或查看: tail -50 /var/log/assistance-management-system/app.log"
        exit 1
    fi
    sleep 1
done

# ── 3. 打开浏览器（多级检测） ──
log "正在打开浏览器..."

_open_browser() {
    local url="$1"
    # 按优先级尝试各浏览器
    for browser in kylin-browser chromium-browser chromium firefox-esr firefox google-chrome; do
        if command -v "$browser" &>/dev/null; then
            log "使用浏览器: $browser"
            "$browser" "$url" &>/dev/null &
            return 0
        fi
    done
    # 回退: xdg-open
    if command -v xdg-open &>/dev/null; then
        xdg-open "$url" &>/dev/null &
        return 0
    fi
    # 最终回退: 打印提示
    warn "未找到浏览器，请手动打开浏览器访问:"
    warn "  $url"
    return 1
}

_open_browser "$BROWSER_URL"

log "系统已启动"
log "访问地址: $BROWSER_URL"
log "关闭服务: sudo systemctl stop $APP_NAME"
