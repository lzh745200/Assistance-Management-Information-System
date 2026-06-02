#!/bin/bash
# DEB包测试脚本 - 麒麟v10系统

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

APP_NAME="military-rural-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=$(python3 -c "import json; print(json.load(open('${SCRIPT_DIR}/../../package.json'))['version'])" 2>/dev/null || echo "1.0.4")
DEB_FILE="${APP_NAME}_${VERSION}_arm64.deb"

echo_info "========================================="
echo_info "  DEB包测试脚本"
echo_info "  目标系统: 麒麟v10 (ARM64)"
echo_info "========================================="
echo ""

# 检查DEB文件
if [ ! -f "$DEB_FILE" ]; then
    echo_error "DEB文件不存在: $DEB_FILE"
    echo_info "请先运行: ./build-deb.sh"
    exit 1
fi

echo_info "找到DEB包: $DEB_FILE"
echo_info "包大小: $(du -h "$DEB_FILE" | cut -f1)"
echo ""

# 检查系统
echo_info "检查系统信息..."
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Kernel: $(uname -r)"
echo "  Arch: $(uname -m)"
echo ""

# 检查依赖
echo_info "检查依赖..."

check_command() {
    if command -v $1 &> /dev/null; then
        echo_info "  ✓ $1 已安装"
        return 0
    else
        echo_warn "  ✗ $1 未安装"
        return 1
    fi
}

MISSING_DEPS=0

if ! check_command docker; then
    MISSING_DEPS=1
fi

if ! check_command docker-compose; then
    MISSING_DEPS=1
fi

if ! check_command curl; then
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo_warn "缺少依赖，尝试安装..."
    echo_info "运行: sudo apt-get update && sudo apt-get install -y docker.io docker-compose curl"
    read -p "是否现在安装？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose curl
    else
        echo_error "请手动安装依赖后再运行测试"
        exit 1
    fi
fi

echo ""

# 测试1: 安装DEB包
echo_info "========================================="
echo_info "  测试1: 安装DEB包"
echo_info "========================================="

echo_info "安装 $DEB_FILE..."
sudo dpkg -i "$DEB_FILE" || {
    echo_error "安装失败"
    sudo apt-get install -f
    exit 1
}

echo_info "✓ 安装成功"
echo ""

# 测试2: 检查文件
echo_info "========================================="
echo_info "  测试2: 检查安装文件"
echo_info "========================================="

check_file() {
    if [ -e "$1" ]; then
        echo_info "  ✓ $1"
        return 0
    else
        echo_error "  ✗ $1 不存在"
        return 1
    fi
}

check_file "/opt/${APP_NAME}"
check_file "/opt/${APP_NAME}/docker-compose.yml"
check_file "/opt/${APP_NAME}/.env"
check_file "/usr/local/bin/${APP_NAME}"
check_file "/var/lib/${APP_NAME}"
check_file "/var/log/${APP_NAME}"

echo ""

# 测试3: 启动服务
echo_info "========================================="
echo_info "  测试3: 启动服务"
echo_info "========================================="

echo_info "启动服务..."
sudo ${APP_NAME} start

echo_info "等待服务启动（60秒）..."
sleep 60

echo ""

# 测试4: 检查服务状态
echo_info "========================================="
echo_info "  测试4: 检查服务状态"
echo_info "========================================="

echo_info "Docker容器状态:"
sudo ${APP_NAME} status

echo ""

# 测试5: 健康检查
echo_info "========================================="
echo_info "  测试5: 健康检查"
echo_info "========================================="

test_endpoint() {
    local url=$1
    local name=$2

    echo_info "测试 $name: $url"
    if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
        echo_info "  ✓ $name 正常"
        return 0
    else
        echo_error "  ✗ $name 失败"
        return 1
    fi
}

HEALTH_FAILED=0

test_endpoint "http://localhost:8000/api/v1/health" "后端健康检查" || HEALTH_FAILED=1
test_endpoint "http://localhost/" "前端访问" || HEALTH_FAILED=1
test_endpoint "http://localhost:9090/-/healthy" "Prometheus" || HEALTH_FAILED=1
test_endpoint "http://localhost:3000/api/health" "Grafana" || HEALTH_FAILED=1

echo ""

# 测试6: 功能测试
echo_info "========================================="
echo_info "  测试6: 功能测试"
echo_info "========================================="

echo_info "测试后端API..."
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
echo "  响应: $API_RESPONSE"

if echo "$API_RESPONSE" | grep -q "healthy\|ok"; then
    echo_info "  ✓ API响应正常"
else
    echo_error "  ✗ API响应异常"
    HEALTH_FAILED=1
fi

echo ""

# 测试7: 日志检查
echo_info "========================================="
echo_info "  测试7: 日志检查"
echo_info "========================================="

echo_info "最近的日志:"
sudo ${APP_NAME} logs --tail=20

echo ""

# 测试8: 资源使用
echo_info "========================================="
echo_info "  测试8: 资源使用"
echo_info "========================================="

echo_info "Docker资源使用:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""

# 测试结果
echo_info "========================================="
echo_info "  测试结果"
echo_info "========================================="

if [ $HEALTH_FAILED -eq 0 ]; then
    echo_info "✓ 所有测试通过！"
    echo ""
    echo_info "系统访问地址:"
    echo_info "  前端: http://localhost"
    echo_info "  后端API: http://localhost:8000"
    echo_info "  API文档: http://localhost:8000/docs"
    echo_info "  监控: http://localhost:3000 (admin/admin123)"
    echo ""
    echo_info "管理命令:"
    echo_info "  启动: sudo ${APP_NAME} start"
    echo_info "  停止: sudo ${APP_NAME} stop"
    echo_info "  重启: sudo ${APP_NAME} restart"
    echo_info "  状态: sudo ${APP_NAME} status"
    echo_info "  日志: sudo ${APP_NAME} logs"
    echo ""
    echo_info "配置文件: /opt/${APP_NAME}/.env"
    echo_info "数据目录: /var/lib/${APP_NAME}"
    echo_info "日志目录: /var/log/${APP_NAME}"
    echo ""
else
    echo_error "✗ 部分测试失败"
    echo_warn "请检查日志: sudo ${APP_NAME} logs"
    exit 1
fi

# 询问是否保留
echo ""
read -p "是否保留安装的系统？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_info "卸载系统..."
    sudo ${APP_NAME} stop
    sudo dpkg --purge ${APP_NAME}
    echo_info "✓ 已卸载"
fi

echo ""
echo_info "========================================="
echo_info "  测试完成！"
echo_info "========================================="
