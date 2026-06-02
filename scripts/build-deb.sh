#!/bin/bash
# ============================================================
# 军队乡村振兴管理系统 - DEB 包自动化构建脚本
# 版本: 1.0.4
# 平台: Linux (amd64/arm64) | Windows (Git Bash/WSL)
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
VERSION="${VERSION:-1.1.0}"
ARCH="${ARCH:-amd64}"
APP_NAME="military-rural-system"
DOCKER_IMAGE="${APP_NAME}-deb-builder"
OUTPUT_DIR="dist/deb"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKERFILE="${PROJECT_ROOT}/docker/Dockerfile.deb-complete"

# 帮助信息
show_help() {
    echo ""
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}  军队乡村振兴管理系统 - DEB 构建脚本${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  amd64              构建 amd64 架构 DEB (默认)"
    echo "  arm64              构建 arm64 架构 DEB"
    echo "  all                构建双架构 DEB (amd64 + arm64)"
    echo "  clean              清理构建产物"
    echo "  help, -h           显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  VERSION=x.x.x      指定版本号 (默认: 1.0.4)"
    echo "  OUTPUT_DIR=path    指定输出目录 (默认: dist/deb)"
    echo ""
    echo "示例:"
    echo "  $0 amd64                       # 构建 amd64 版本"
    echo "  $0 arm64                       # 构建 arm64 版本"
    echo "  $0 all                         # 构建双架构版本"
    echo "  VERSION=1.0.5 $0 amd64         # 指定版本构建"
    echo "  $0 clean                       # 清理构建产物"
    echo ""
    echo -e "${BLUE}==============================================${NC}"
    echo ""
}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查前置条件
check_prerequisites() {
    log_info "检查前置条件..."

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未运行"
        log_error "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行或当前用户没有 Docker 权限"
        log_error "请确保 Docker 守护进程正在运行"
        exit 1
    fi

    # 检查 docker buildx
    if ! docker buildx version &> /dev/null; then
        log_warning "docker buildx 不可用，尝试初始化..."
        docker buildx create --use default 2>/dev/null || true
    fi

    # 检查 Dockerfile
    if [ ! -f "$DOCKERFILE" ]; then
        log_error "Dockerfile 不存在: $DOCKERFILE"
        exit 1
    fi

    # 检查项目目录
    if [ ! -d "$PROJECT_ROOT/frontend" ] || [ ! -d "$PROJECT_ROOT/backend" ]; then
        log_error "项目目录结构不完整"
        exit 1
    fi

    log_success "前置条件检查通过"
}

# 创建输出目录
prepare_output() {
    log_info "准备输出目录: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
}

# 构建单架构 DEB
build_single_arch() {
    local target_arch=$1
    local docker_arch

    case $target_arch in
        amd64)
            docker_arch="linux/amd64"
            ;;
        arm64)
            docker_arch="linux/arm64"
            ;;
        *)
            log_error "不支持的架构: $target_arch"
            exit 1
            ;;
    esac

    local tag="${DOCKER_IMAGE}:${VERSION}-${target_arch}"
    local deb_file="${APP_NAME}_${VERSION}_${target_arch}.deb"

    log_info "=============================================="
    log_info "  开始构建 DEB 包"
    log_info "  版本: ${VERSION}"
    log_info "  架构: ${target_arch}"
    log_info "  目标平台: ${docker_arch}"
    log_info "=============================================="

    # 执行 Docker 构建
    log_info "执行 Docker 构建..."

    if docker buildx build \
        --platform "$docker_arch" \
        --build-arg VERSION="$VERSION" \
        --build-arg TARGETARCH="$target_arch" \
        -t "$tag" \
        -f "$DOCKERFILE" \
        --output type=local,dest="$OUTPUT_DIR" \
        --progress=plain \
        "$PROJECT_ROOT" 2>&1; then

        log_success "Docker 构建完成"

        # 查找并移动 DEB 文件（如果不在正确位置）
        local found_deb
        found_deb=$(find "$OUTPUT_DIR" -name "*.deb" -type f 2>/dev/null | head -1)

        if [ -n "$found_deb" ] && [ -f "$found_deb" ]; then
            local expected_deb="$OUTPUT_DIR/$deb_file"
            if [ "$found_deb" != "$expected_deb" ]; then
                log_info "重命名 DEB 文件: $(basename $found_deb) -> $deb_file"
                mv "$found_deb" "$expected_deb"
            fi

            log_success "=============================================="
            log_success "  DEB 包构建成功！"
            log_success "=============================================="
            log_info ""
            log_info "  文件: $OUTPUT_DIR/$deb_file"
            log_info "  大小: $(ls -lh "$OUTPUT_DIR/$deb_file" | awk '{print $5}')"
            log_info "  SHA256: $(sha256sum "$OUTPUT_DIR/$deb_file" | awk '{print $1}')"
            log_info ""
            log_info "  安装方法:"
            log_info "    sudo dpkg -i $OUTPUT_DIR/$deb_file"
            log_info "    sudo apt-get install -f  # 自动安装依赖"
            log_info ""
            log_info "  或使用 systemd 服务:"
            log_info "    sudo systemctl start ${APP_NAME}.service"
            log_info "    sudo systemctl enable ${APP_NAME}.service"
            log_success ""
        else
            log_error "未找到生成的 DEB 文件"
            log_info "检查输出目录: $OUTPUT_DIR"
            ls -la "$OUTPUT_DIR" 2>/dev/null || true
            exit 1
        fi
    else
        log_error "Docker 构建失败"
        log_error "请检查 Docker 日志以获取详细信息"
        exit 1
    fi
}

# 构建双架构 DEB
build_all_arch() {
    log_info "=============================================="
    log_info "  开始构建双架构 DEB 包"
    log_info "  版本: ${VERSION}"
    log_info "=============================================="

    # 检查 docker buildx 是否支持多架构
    if ! docker buildx version &> /dev/null; then
        log_error "docker buildx 不可用，无法构建多架构"
        exit 1
    fi

    # 确保 buildx 使用默认驱动
    docker buildx create --use default 2>/dev/null || true

    # 执行多架构构建
    log_info "执行 Docker 多架构构建 (amd64 + arm64)..."

    if docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --build-arg VERSION="$VERSION" \
        -t "${DOCKER_IMAGE}:${VERSION}" \
        -f "$DOCKERFILE" \
        --output type=local,dest="$OUTPUT_DIR" \
        --progress=plain \
        "$PROJECT_ROOT" 2>&1; then

        log_success "Docker 多架构构建完成"

        # 列出生成的文件
        log_info "生成的 DEB 文件:"
        ls -lh "$OUTPUT_DIR"/*.deb 2>/dev/null || log_warning "未找到 DEB 文件"

    else
        log_error "Docker 多架构构建失败"
        log_error "回退到单架构构建..."

        # 回退到 amd64
        build_single_arch amd64
    fi
}

# 清理构建产物
clean() {
    log_info "清理构建产物..."

    # 清理输出目录
    rm -rf "${PROJECT_ROOT}/${OUTPUT_DIR}"

    # 清理后端构建产物
    rm -rf "${PROJECT_ROOT}/backend/dist_x64"
    rm -rf "${PROJECT_ROOT}/backend/dist_arm64"
    rm -rf "${PROJECT_ROOT}/backend/dist_output"
    rm -rf "${PROJECT_ROOT}/backend/dist_${ARCH}"
    rm -rf "${PROJECT_ROOT}/backend/build"
    rm -rf "${PROJECT_ROOT}/backend/*.spec"

    # 清理前端构建产物
    rm -rf "${PROJECT_ROOT}/frontend/dist"

    # 清理 DEB 包结构
    rm -rf "${PROJECT_ROOT}/pkg"

    # 清理 Docker 镜像
    log_info "清理 Docker 镜像..."
    docker rmi "${DOCKER_IMAGE}:${VERSION}-amd64" 2>/dev/null || true
    docker rmi "${DOCKER_IMAGE}:${VERSION}-arm64" 2>/dev/null || true
    docker rmi "${DOCKER_IMAGE}:${VERSION}" 2>/dev/null || true

    log_success "清理完成"
}

# 显示构建环境信息
show_env_info() {
    log_info "=============================================="
    log_info "  构建环境信息"
    log_info "=============================================="
    log_info "  项目目录: $PROJECT_ROOT"
    log_info "  版本: $VERSION"
    log_info "  架构: $ARCH"
    log_info "  输出目录: $OUTPUT_DIR"
    log_info "  Dockerfile: $DOCKERFILE"
    log_info "  Docker 版本: $(docker --version 2>/dev/null || echo 'N/A')"
    log_info "  Buildx 版本: $(docker buildx version 2>/dev/null || echo 'N/A')"
    log_info "=============================================="
}

# 主函数
main() {
    # 切换到项目根目录
    cd "$PROJECT_ROOT"

    # 解析参数
    case "${1:-amd64}" in
        amd64)
            check_prerequisites
            prepare_output
            show_env_info
            build_single_arch amd64
            ;;
        arm64)
            check_prerequisites
            prepare_output
            show_env_info
            build_single_arch arm64
            ;;
        all)
            check_prerequisites
            prepare_output
            show_env_info
            build_all_arch
            ;;
        clean)
            clean
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            log_error "未知参数: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
