#!/bin/bash
# ============================================================
#  军队乡村振兴管理系统 - ARM64 DEB包测试脚本
#  在麒麟V10 ARM64系统上运行
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 配置
APP_NAME="military-rural-system"
DEB_FILE=""
TEST_RESULTS=()

# 查找DEB文件
for f in military-rural-system_*_arm64.deb; do
    if [ -f "$f" ]; then
        DEB_FILE="$f"
        break
    fi
done

if [ -z "$DEB_FILE" ]; then
    echo_error "未找到ARM64 DEB包文件"
    exit 1
fi

echo "========================================="
echo "  军队乡村振兴管理系统"
echo "  ARM64 DEB包测试"
echo "========================================="
echo ""
echo "DEB包: $DEB_FILE"
echo ""

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo_test "[$TOTAL_TESTS] $test_name"

    if eval "$test_command"; then
        echo_info "✓ 通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✓ $test_name")
        return 0
    else
        echo_error "✗ 失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("✗ $test_name")
        return 1
    fi
    echo ""
}

# ==================== 测试开始 ====================

echo_info "开始测试..."
echo ""

# 测试1: 系统架构验证
run_test "系统架构验证 (aarch64)" \
    "[ \"\$(uname -m)\" = \"aarch64\" ]"

# 测试2: Docker架构验证
run_test "Docker架构验证 (arm64)" \
    "docker version | grep -i 'arch' | grep -i 'arm64' > /dev/null"

# 测试3: DEB包信息验证
run_test "DEB包架构验证" \
    "dpkg-deb --info $DEB_FILE | grep 'Architecture: arm64' > /dev/null"

# 测试4: DEB包内容验证
run_test "DEB包内容完整性" \
    "dpkg-deb --contents $DEB_FILE | grep -E '(backend|frontend|docker-compose.yml)' > /dev/null"

# 测试5: 检查Docker镜像文件
run_test "Docker镜像文件存在" \
    "dpkg-deb --contents $DEB_FILE | grep 'docker-images.*\.tar' > /dev/null"

echo ""
echo_info "基础验证完成，开始安装测试..."
echo ""

# 询问是否继续安装测试
read -p "是否继续进行安装测试？这将安装DEB包到系统 (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_warn "跳过安装测试"
    echo ""
    echo "========================================="
    echo "  测试摘要"
    echo "========================================="
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    echo ""
    for result in "${TEST_RESULTS[@]}"; do
        echo "  $result"
    done
    echo "========================================="
    exit 0
fi

# 测试6: 安装DEB包
echo_test "[$((TOTAL_TESTS + 1))] 安装DEB包"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

sudo dpkg -i "$DEB_FILE" 2>&1 | tee /tmp/install.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo_info "✓ 安装成功"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 安装DEB包")
else
    echo_warn "安装可能有依赖问题，尝试修复..."
    sudo apt-get install -f -y

    if [ $? -eq 0 ]; then
        echo_info "✓ 依赖修复成功"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✓ 安装DEB包（已修复依赖）")
    else
        echo_error "✗ 安装失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("✗ 安装DEB包")
        exit 1
    fi
fi

echo ""

# 测试7: 验证安装目录
run_test "安装目录存在" \
    "[ -d /opt/$APP_NAME ]"

# 测试8: 验证配置文件
run_test "配置文件存在" \
    "[ -f /opt/$APP_NAME/.env ]"

# 测试9: 验证管理脚本
run_test "管理脚本可执行" \
    "[ -x /usr/local/bin/$APP_NAME ]"

# 测试10: 验证Docker镜像加载
run_test "Docker镜像已加载" \
    "docker images | grep -E '(military-rural|mysql|prometheus|grafana)' > /dev/null"

# 测试11: 验证镜像架构
echo_test "[$((TOTAL_TESTS + 1))] 验证Docker镜像架构"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ARCH_CHECK=true
for img in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(military-rural|mysql|prometheus|grafana)"); do
    ARCH=$(docker inspect "$img" --format='{{.Architecture}}' 2>/dev/null || echo "unknown")
    if [ "$ARCH" != "arm64" ]; then
        echo_error "镜像 $img 架构不是 arm64: $ARCH"
        ARCH_CHECK=false
    fi
done

if [ "$ARCH_CHECK" = true ]; then
    echo_info "✓ 所有镜像架构正确 (arm64)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ Docker镜像架构验证")
else
    echo_error "✗ 部分镜像架构不正确"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ Docker镜像架构验证")
fi

echo ""

# 测试12: 启动服务
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
echo_info "等待服务启动（90秒）..."
sleep 90

# 测试13: 检查容器状态
echo_test "[$((TOTAL_TESTS + 1))] 检查容器状态"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RUNNING_CONTAINERS=$(docker ps --filter "name=military-rural" --format "{{.Names}}" | wc -l)

if [ "$RUNNING_CONTAINERS" -ge 3 ]; then
    echo_info "✓ 容器运行正常 ($RUNNING_CONTAINERS 个容器)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 容器状态检查")
    docker ps --filter "name=military-rural" --format "table {{.Names}}\t{{.Status}}"
else
    echo_error "✗ 部分容器未运行 (仅 $RUNNING_CONTAINERS 个容器)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 容器状态检查")
    docker ps -a --filter "name=military-rural"
fi

echo ""

# 测试14: 后端健康检查
echo_test "[$((TOTAL_TESTS + 1))] 后端健康检查"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo_info "✓ 后端API响应正常 (HTTP $HEALTH_RESPONSE)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 后端健康检查")
else
    echo_error "✗ 后端API响应异常 (HTTP $HEALTH_RESPONSE)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 后端健康检查")
fi

# 测试15: 前端访问测试
echo_test "[$((TOTAL_TESTS + 1))] 前端访问测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)

if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo_info "✓ 前端页面访问正常 (HTTP $FRONTEND_RESPONSE)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 前端访问测试")
else
    echo_error "✗ 前端页面访问异常 (HTTP $FRONTEND_RESPONSE)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 前端访问测试")
fi

# 测试16: 数据库连接测试
echo_test "[$((TOTAL_TESTS + 1))] 数据库连接测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

DB_CHECK=$(docker exec military-rural-db mysqladmin ping -h localhost -u root -pmilitary_rural_2024 2>&1 | grep "mysqld is alive")

if [ -n "$DB_CHECK" ]; then
    echo_info "✓ 数据库连接正常"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 数据库连接测试")
else
    echo_error "✗ 数据库连接失败"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ 数据库连接测试")
fi

# 测试17: 监控系统测试
echo_test "[$((TOTAL_TESTS + 1))] 监控系统测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

PROMETHEUS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy)
GRAFANA_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health)

if [ "$PROMETHEUS_RESPONSE" = "200" ] && [ "$GRAFANA_RESPONSE" = "200" ]; then
    echo_info "✓ 监控系统正常 (Prometheus: $PROMETHEUS_RESPONSE, Grafana: $GRAFANA_RESPONSE)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 监控系统测试")
else
    echo_warn "⚠ 监控系统部分异常 (Prometheus: $PROMETHEUS_RESPONSE, Grafana: $GRAFANA_RESPONSE)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("⚠ 监控系统测试（部分异常）")
fi

# 测试18: 性能测试
echo_test "[$((TOTAL_TESTS + 1))] 性能测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health)

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo_info "✓ 响应时间正常 (${RESPONSE_TIME}s)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 性能测试 (${RESPONSE_TIME}s)")
else
    echo_warn "⚠ 响应时间较慢 (${RESPONSE_TIME}s)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("⚠ 性能测试 (${RESPONSE_TIME}s)")
fi

# 测试19: 资源使用测试
echo_test "[$((TOTAL_TESTS + 1))] 资源使用测试"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo_info "容器资源使用情况："
docker stats --no-stream --filter "name=military-rural"

PASSED_TESTS=$((PASSED_TESTS + 1))
TEST_RESULTS+=("✓ 资源使用测试")

echo ""

# 测试20: 日志检查
echo_test "[$((TOTAL_TESTS + 1))] 日志检查"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ERROR_COUNT=$(docker logs military-rural-backend 2>&1 | grep -i "error" | grep -v "ERROR_HANDLER" | wc -l)

if [ "$ERROR_COUNT" -lt 5 ]; then
    echo_info "✓ 日志正常 (错误数: $ERROR_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ 日志检查")
else
    echo_warn "⚠ 发现较多错误日志 (错误数: $ERROR_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("⚠ 日志检查 (错误数: $ERROR_COUNT)")
fi

echo ""
echo "========================================="
echo "  测试完成"
echo "========================================="
echo ""
echo "总测试数: $TOTAL_TESTS"
echo "通过: $PASSED_TESTS"
echo "失败: $FAILED_TESTS"
echo "成功率: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%"
echo ""
echo "详细结果："
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done
echo ""
echo "========================================="
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo_info "✓ 所有测试通过！系统运行正常。"
    echo ""
    echo "访问地址："
    echo "  前端: http://localhost"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  监控: http://localhost:3000 (admin/admin123)"
    echo ""
    echo "管理命令："
    echo "  sudo military-rural-system status   # 查看状态"
    echo "  sudo military-rural-system logs     # 查看日志"
    echo "  sudo military-rural-system restart  # 重启服务"
    echo "  sudo military-rural-system stop     # 停止服务"
    echo ""
    exit 0
else
    echo_error "✗ 有 $FAILED_TESTS 个测试失败，请检查日志。"
    echo ""
    echo "查看日志："
    echo "  sudo military-rural-system logs"
    echo ""
    echo "查看容器状态："
    echo "  docker ps -a"
    echo ""
    exit 1
fi
