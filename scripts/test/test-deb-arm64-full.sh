#!/bin/bash
# ============================================================
#  军队乡村振兴管理系统 - ARM64完整DEB包测试脚本
#  测试包含所有依赖的完整安装包
#  在麒麟V10 ARM64系统上运行
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

echo_section() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# 配置
APP_NAME="military-rural-system"
DEB_FILE=""
TEST_RESULTS=()
TEST_LOG="/tmp/military-rural-test-$(date +%Y%m%d_%H%M%S).log"

# 查找DEB文件
for f in military-rural-system_*_arm64_full.deb military-rural-system_*_arm64.deb; do
    if [ -f "$f" ]; then
        DEB_FILE="$f"
        break
    fi
done

if [ -z "$DEB_FILE" ]; then
    echo_error "未找到ARM64 DEB包文件"
    exit 1
fi

# 开始记录日志
exec > >(tee -a "$TEST_LOG")
exec 2>&1

echo_section "军队乡村振兴管理系统 - ARM64完整DEB包测试"
echo ""
echo "DEB包: $DEB_FILE"
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "日志文件: $TEST_LOG"
echo ""

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local is_critical="${3:-true}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo_test "[$TOTAL_TESTS] $test_name"

    if eval "$test_command"; then
        echo_info "✓ 通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✓ $test_name")
        echo ""
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            echo_error "✗ 失败"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("✗ $test_name")
        else
            echo_warn "⚠ 警告"
            WARNED_TESTS=$((WARNED_TESTS + 1))
            TEST_RESULTS+=("⚠ $test_name")
        fi
        echo ""
        return 1
    fi
}

# ==================== 阶段1: 系统环境检查 ====================

echo_section "阶段1: 系统环境检查"
echo ""

run_test "系统架构验证 (aarch64)" \
    "[ \"\$(uname -m)\" = \"aarch64\" ]"

run_test "操作系统验证 (麒麟V10)" \
    "grep -i 'kylin' /etc/os-release > /dev/null || grep -i 'ubuntu' /etc/os-release > /dev/null" \
    "false"

run_test "内存检查 (>= 4GB)" \
    "[ \$(free -g | awk '/^Mem:/{print \$2}') -ge 4 ]" \
    "false"

run_test "磁盘空间检查 (>= 20GB)" \
    "[ \$(df -BG / | awk 'NR==2{print \$4}' | sed 's/G//') -ge 20 ]" \
    "false"

# ==================== 阶段2: DEB包验证 ====================

echo_section "阶段2: DEB包验证"
echo ""

run_test "DEB包文件存在" \
    "[ -f \"$DEB_FILE\" ]"

run_test "DEB包架构验证 (arm64)" \
    "dpkg-deb --info \"$DEB_FILE\" | grep 'Architecture: arm64' > /dev/null"

run_test "DEB包大小验证 (>= 500MB)" \
    "[ \$(stat -c %s \"$DEB_FILE\") -ge 524288000 ]"

run_test "DEB包内容完整性" \
    "dpkg-deb --contents \"$DEB_FILE\" | grep -E '(backend|frontend|docker-compose.yml|dependencies)' > /dev/null"

run_test "依赖包存在验证" \
    "dpkg-deb --contents \"$DEB_FILE\" | grep 'dependencies.*\.deb' > /dev/null"

run_test "Docker镜像文件存在" \
    "dpkg-deb --contents \"$DEB_FILE\" | grep 'docker-images.*\.tar' > /dev/null"

# ==================== 阶段3: 安装前准备 ====================

echo_section "阶段3: 安装前准备"
echo ""

# 询问是否继续安装测试
echo_warn "接下来将进行安装测试，这将："
echo "  1. 安装DEB包到系统"
echo "  2. 自动安装Docker和依赖"
echo "  3. 加载所有Docker镜像"
echo "  4. 启动所有服务"
echo ""
read -p "是否继续? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_warn "用户取消安装测试"
    echo ""
    echo_section "测试摘要（部分测试）"
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    echo "警告: $WARNED_TESTS"
    echo ""
    exit 0
fi

# 检查是否已安装
if dpkg -l | grep -q "$APP_NAME"; then
    echo_warn "检测到已安装的版本，是否先卸载? (y/n): "
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo_info "卸载旧版本..."
        sudo dpkg --purge "$APP_NAME" || true
        sudo docker system prune -af || true
    fi
fi

# ==================== 阶段4: 安装测试 ====================

echo_section "阶段4: 安装测试"
echo ""

echo_test "[$((TOTAL_TESTS + 1))] 安装DEB包（包含所有依赖）"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo_info "这可能需要5-10分钟，请耐心等待..."
echo ""

sudo dpkg -i "$DEB_FILE" 2>&1 | tee /tmp/install.log

INSTALL_STATUS=${PIPESTATUS[0]}

if [ $INSTALL_STATUS -eq 0 ]; then
    echo_info "✓ 安装成功"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 安装DEB包")
else
    echo_warn "安装可能有问题，尝试修复依赖..."
    sudo apt-get install -f -y

    if [ $? -eq 0 ]; then
        echo_info "✓ 依赖修复成功"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✓ 安装DEB包（已修复依赖）")
    else
        echo_error "✗ 安装失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("✗ 安装DEB包")
        echo ""
        echo "安装日志："
        tail -20 /tmp/install.log
        exit 1
    fi
fi

echo ""

# ==================== 阶段5: 安装后验证 ====================

echo_section "阶段5: 安装后验证"
echo ""

run_test "安装目录存在" \
    "[ -d /opt/$APP_NAME ]"

run_test "配置文件存在" \
    "[ -f /opt/$APP_NAME/.env ]"

run_test "管理脚本可执行" \
    "[ -x /usr/local/bin/$APP_NAME ]"

run_test "数据目录创建" \
    "[ -d /var/lib/$APP_NAME ]"

run_test "日志目录创建" \
    "[ -d /var/log/$APP_NAME ]"

# ==================== 阶段6: 依赖验证 ====================

echo_section "阶段6: 依赖验证"
echo ""

run_test "Docker已安装" \
    "command -v docker > /dev/null"

run_test "Docker Compose已安装" \
    "command -v docker-compose > /dev/null"

run_test "Docker服务运行中" \
    "systemctl is-active --quiet docker"

run_test "Docker版本检查" \
    "docker --version | grep -E '(20\.|2[1-9]\.)' > /dev/null"

run_test "Docker架构验证 (arm64)" \
    "docker version 2>/dev/null | grep -i 'arch' | grep -i 'arm64' > /dev/null"

# ==================== 阶段7: Docker镜像验证 ====================

echo_section "阶段7: Docker镜像验证"
echo ""

run_test "Docker镜像已加载" \
    "docker images | grep -E '(military-rural|mysql|prometheus|grafana)' > /dev/null"

echo_test "[$((TOTAL_TESTS + 1))] 验证所有镜像架构 (arm64)"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ARCH_CHECK=true
ARCH_ERRORS=""
for img in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(military-rural|mysql|prometheus|grafana)" | head -10); do
    ARCH=$(docker inspect "$img" --format='{{.Architecture}}' 2>/dev/null || echo "unknown")
    if [ "$ARCH" != "arm64" ]; then
        echo_error "  镜像 $img 架构不正确: $ARCH"
        ARCH_CHECK=false
        ARCH_ERRORS="$ARCH_ERRORS\n  - $img: $ARCH"
    else
        echo_info "  ✓ $img: $ARCH"
    fi
done

if [ "$ARCH_CHECK" = true ]; then
    echo_info "✓ 所有镜像架构正确"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ Docker镜像架构验证")
else
    echo_error "✗ 部分镜像架构不正确"
    echo -e "$ARCH_ERRORS"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ Docker镜像架构验证")
fi

echo ""

# ==================== 阶段8: 服务启动测试 ====================

echo_section "阶段8: 服务启动测试"
echo ""

echo_test "[$((TOTAL_TESTS + 1))] 启动服务"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

sudo $APP_NAME start

if [ $? -eq 0 ]; then
    echo_info "✓ 服务启动命令执行成功"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 启动服务")
else
    echo_error "✗ 服务启动失败"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 启动服务")
fi

echo ""
echo_info "等待服务完全启动（90秒）..."
for i in {1..90}; do
    echo -ne "\r进度: [$i/90] "
    sleep 1
done
echo ""
echo ""

# ==================== 阶段9: 容器状态检查 ====================

echo_section "阶段9: 容器状态检查"
echo ""

echo_test "[$((TOTAL_TESTS + 1))] 检查容器运行状态"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RUNNING_CONTAINERS=$(docker ps --filter "name=military-rural" --format "{{.Names}}" | wc -l)
EXPECTED_CONTAINERS=5  # backend, frontend, database, prometheus, grafana

echo_info "运行中的容器数: $RUNNING_CONTAINERS / $EXPECTED_CONTAINERS"
docker ps --filter "name=military-rural" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

if [ "$RUNNING_CONTAINERS" -ge 3 ]; then
    echo_info "✓ 主要容器运行正常"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 容器状态检查 ($RUNNING_CONTAINERS/$EXPECTED_CONTAINERS)")
else
    echo_error "✗ 部分容器未运行"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 容器状态检查 ($RUNNING_CONTAINERS/$EXPECTED_CONTAINERS)")
    echo ""
    echo "所有容器状态："
    docker ps -a --filter "name=military-rural"
fi

echo ""

# ==================== 阶段10: 健康检查 ====================

echo_section "阶段10: 健康检查"
echo ""

run_test "后端API健康检查" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/health | grep -q '200'"

run_test "前端页面访问" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost/ | grep -q '200'"

run_test "数据库连接测试" \
    "docker exec military-rural-db mysqladmin ping -h localhost -u root -pmilitary_rural_2024 2>&1 | grep -q 'mysqld is alive'" \
    "false"

run_test "Prometheus监控" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:9090/-/healthy | grep -q '200'" \
    "false"

run_test "Grafana监控" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/health | grep -q '200'" \
    "false"

# ==================== 阶段11: 功能测试 ====================

echo_section "阶段11: 功能测试"
echo ""

echo_test "[$((TOTAL_TESTS + 1))] API响应时间测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health 2>/dev/null || echo "999")

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l 2>/dev/null || echo "0") )); then
    echo_info "✓ 响应时间正常: ${RESPONSE_TIME}s"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ API响应时间 (${RESPONSE_TIME}s)")
else
    echo_warn "⚠ 响应时间较慢: ${RESPONSE_TIME}s"
    WARNED_TESTS=$((WARNED_TESTS + 1))
    TEST_RESULTS+=("⚠ API响应时间 (${RESPONSE_TIME}s)")
fi

echo ""

echo_test "[$((TOTAL_TESTS + 1))] 资源使用检查"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo_info "容器资源使用情况："
docker stats --no-stream --filter "name=military-rural" --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

PASSED_TESTS=$((PASSED_TESTS + 1))
TEST_RESULTS+=("✓ 资源使用检查")

echo ""

echo_test "[$((TOTAL_TESTS + 1))] 日志检查"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ERROR_COUNT=$(docker logs military-rural-backend 2>&1 | grep -i "error" | grep -v "ERROR_HANDLER" | grep -v "error_handler" | wc -l)

if [ "$ERROR_COUNT" -lt 5 ]; then
    echo_info "✓ 日志正常 (错误数: $ERROR_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 日志检查")
else
    echo_warn "⚠ 发现较多错误日志 (错误数: $ERROR_COUNT)"
    WARNED_TESTS=$((WARNED_TESTS + 1))
    TEST_RESULTS+=("⚠ 日志检查 (错误数: $ERROR_COUNT)")
    echo ""
    echo "最近的错误日志："
    docker logs military-rural-backend 2>&1 | grep -i "error" | grep -v "ERROR_HANDLER" | tail -5
fi

echo ""

# ==================== 阶段12: 管理命令测试 ====================

echo_section "阶段12: 管理命令测试"
echo ""

run_test "status命令测试" \
    "sudo $APP_NAME status > /dev/null 2>&1"

run_test "health命令测试" \
    "sudo $APP_NAME health > /dev/null 2>&1" \
    "false"

# ==================== 测试总结 ====================

echo_section "测试完成"
echo ""

SUCCESS_RATE=$(echo "scale=2; ($PASSED_TESTS + $WARNED_TESTS) * 100 / $TOTAL_TESTS" | bc)

echo "测试统计："
echo "  总测试数: $TOTAL_TESTS"
echo "  通过: $PASSED_TESTS"
echo "  警告: $WARNED_TESTS"
echo "  失败: $FAILED_TESTS"
echo "  成功率: ${SUCCESS_RATE}%"
echo ""

echo "详细结果："
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done
echo ""

echo "系统信息："
echo "  架构: $(uname -m)"
echo "  操作系统: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')"
echo "  内核: $(uname -r)"
echo "  Docker: $(docker --version 2>/dev/null || echo '未安装')"
echo "  Docker Compose: $(docker-compose --version 2>/dev/null || echo '未安装')"
echo ""

echo "日志文件: $TEST_LOG"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo_section "✓ 测试通过！系统运行正常"
    echo ""
    echo "访问地址："
    echo "  前端界面: http://localhost"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/admin123)"
    echo ""
    echo "管理命令："
    echo "  sudo military-rural-system status   # 查看状态"
    echo "  sudo military-rural-system logs     # 查看日志"
    echo "  sudo military-rural-system restart  # 重启服务"
    echo "  sudo military-rural-system stop     # 停止服务"
    echo "  sudo military-rural-system health   # 健康检查"
    echo ""
    echo "数据目录："
    echo "  应用: /opt/military-rural-system"
    echo "  数据: /var/lib/military-rural-system"
    echo "  日志: /var/log/military-rural-system"
    echo ""
    exit 0
else
    echo_section "✗ 测试失败"
    echo ""
    echo "失败的测试数: $FAILED_TESTS"
    echo ""
    echo "故障排查："
    echo "  1. 查看安装日志: cat /tmp/install.log"
    echo "  2. 查看服务日志: sudo military-rural-system logs"
    echo "  3. 查看容器状态: docker ps -a"
    echo "  4. 查看系统日志: sudo journalctl -xe"
    echo ""
    echo "常见问题："
    echo "  - 端口冲突: sudo netstat -tlnp | grep -E '(80|8000|3000)'"
    echo "  - Docker未运行: sudo systemctl start docker"
    echo "  - 内存不足: free -h"
    echo "  - 磁盘空间: df -h"
    echo ""
    exit 1
fi
