.PHONY: test test-backend test-frontend test-e2e coverage deploy-check clean \
        build-deb build-deb-amd64 build-deb-arm64 build-deb-all \
        docker-build docker-build-amd64 docker-build-arm64 docker-build-all \
        deb-clean \
        build-kylin build-kylin-arm64 kylin-clean kylin-verify

# 默认运行所有测试
test: test-backend test-frontend
	@echo "✓ 所有测试通过"

# 后端测试
test-backend:
	@echo ">>> 运行后端测试..."
	cd backend && python -m pytest tests/ -v --tb=short --cov=app --cov-fail-under=50

# 前端测试
test-frontend:
	@echo ">>> 运行前端测试..."
	cd frontend && npm run test:coverage

# E2E测试
test-e2e:
	@echo ">>> 运行 E2E 测试..."
	cd frontend && npm run test:e2e

# 生成覆盖率报告
coverage:
	@echo ">>> 生成覆盖率报告..."
	cd backend && python -m pytest --cov=app --cov-report=html --cov-report=xml
	cd frontend && npm run test:coverage

# 部署前检查
deploy-check:
	@echo ">>> 运行部署前检查..."
	# 后端检查
	cd backend && \
		python -m pytest tests/ --cov=app --cov-fail-under=50 && \
		python -m bandit -r app/ -f json -o bandit-report.json || true

	# 前端检查
	cd frontend && \
		npm run lint && \
		npm run type-check && \
		npm run test:run

	@echo "✓ 部署前检查通过"

# 安全扫描
security:
	@echo ">>> 运行安全扫描..."
	cd backend && \
		python -m bandit -r app/ -f json -o bandit-report.json && \
		safety check

# 清理测试产物
clean:
	@echo ">>> 清理测试产物..."
	cd backend && rm -rf .pytest_cache htmlcov coverage.xml .coverage __pycache__
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf coverage playwright-report test-results

# 安装依赖
install:
	@echo ">>> 安装依赖..."
	cd backend && pip install -r requirements.txt && pip install pytest pytest-cov pytest-asyncio
	cd frontend && npm ci

# 运行开发服务器
dev:
	@echo ">>> 启动开发服务器..."
	@echo "后端: http://localhost:8000"
	@echo "前端: http://localhost:5173"
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
	cd frontend && npm run dev

# 构建生产版本
build:
	@echo ">>> 构建生产版本..."
	cd frontend && npm run build
	@echo "✓ 构建完成"

# 打包 Electron
electron-build:
	@echo ">>> 打包 Electron 应用..."
	cd frontend && npm run electron:build
	@echo "✓ Electron 打包完成"

# Windows 安装程序
win-installer: electron-build
	@echo ">>> 构建 Windows 安装程序..."
	cd frontend && npm run electron:build:win
	@echo "✓ Windows 安装程序构建完成"

# ============================================================
# DEB 包构建（Docker 跨平台构建，推荐方式）
# ============================================================

VERSION := $(shell node -p "require('./package.json').version" 2>/dev/null || echo "1.2.0")
APP_NAME := assistance-management-system
OUTPUT_DIR := dist/deb

# Docker 构建 DEB (amd64)
docker-build-amd64:
	@echo "=== Docker 构建 DEB (amd64) ==="
	mkdir -p $(OUTPUT_DIR)
	docker buildx build \
		--platform linux/amd64 \
		--build-arg VERSION=$(VERSION) \
		-t $(APP_NAME)-deb:$(VERSION)-amd64 \
		-f docker/Dockerfile.deb-complete \
		--output type=local,dest=$(OUTPUT_DIR) \
		. 2>&1
	@echo ""
	@echo "=== 构建完成 ==="
	@if [ -f $(OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_amd64.deb ]; then \
		echo "成功: $(OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_amd64.deb"; \
		ls -lh $(OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_amd64.deb; \
	else \
		echo "警告: DEB 文件可能未生成到 $(OUTPUT_DIR)"; \
		ls -lh $(OUTPUT_DIR)/ 2>/dev/null || true; \
	fi

# Docker 构建 DEB (arm64)
docker-build-arm64:
	@echo "=== Docker 构建 DEB (arm64) ==="
	mkdir -p $(OUTPUT_DIR)
	docker buildx build \
		--platform linux/arm64 \
		--build-arg VERSION=$(VERSION) \
		-t $(APP_NAME)-deb:$(VERSION)-arm64 \
		-f docker/Dockerfile.deb-complete \
		--output type=local,dest=$(OUTPUT_DIR) \
		. 2>&1
	@echo ""
	@echo "构建完成，输出到: $(OUTPUT_DIR)"

# Docker 构建（默认 amd64）
docker-build: docker-build-amd64

# Docker 多架构构建
docker-build-all:
	@echo "=== Docker 多架构构建 ==="
	@which docker-buildx > /dev/null || (echo "错误: 需要 docker-buildx" && exit 1)
	docker buildx create --use default 2>/dev/null || true
	mkdir -p $(OUTPUT_DIR)
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--build-arg VERSION=$(VERSION) \
		-t $(APP_NAME)-deb:$(VERSION) \
		-f docker/Dockerfile.deb-complete \
		--output type=local,dest=$(OUTPUT_DIR) \
		--progress=plain \
		. 2>&1
	@echo ""
	@echo "=== 构建完成 ==="
	ls -lh $(OUTPUT_DIR)/*.deb 2>/dev/null || echo "检查输出目录: $(OUTPUT_DIR)"

# 简化目标
build-deb: docker-build-amd64
build-deb-amd64: docker-build-amd64
build-deb-arm64: docker-build-arm64
build-deb-all: docker-build-all

# 清理 DEB 构建产物
deb-clean:
	@echo "=== 清理 DEB 构建产物 ==="
	rm -rf $(OUTPUT_DIR)
	rm -rf backend/dist_x64 backend/dist_arm64 backend/dist_output
	rm -rf frontend/dist
	rm -rf pkg
	docker rmi $(APP_NAME)-deb:$(VERSION)-amd64 2>/dev/null || true
	docker rmi $(APP_NAME)-deb:$(VERSION)-arm64 2>/dev/null || true
	@echo "清理完成"

# ============================================================
# 麒麟 V10 ARM64 一体化单机版（无 Electron，纯 Web 架构）
# ============================================================
KYLIN_OUTPUT_DIR := dist/deb/kylin

# 构建麒麟 V10 ARM64 单机版 DEB
build-kylin-arm64:
	@echo "=== 构建麒麟 V10 ARM64 单机版 DEB ==="
	@echo "版本: $(VERSION)"
	@echo "架构: arm64 (aarch64)"
	@echo "模式: 无 Electron，纯 FastAPI + 系统浏览器"
	@echo ""
	@mkdir -p $(KYLIN_OUTPUT_DIR)
	docker buildx build \
		--platform linux/arm64 \
		--build-arg VERSION=$(VERSION) \
		-t $(APP_NAME)-kylin:$(VERSION) \
		-f docker/Dockerfile.kylin-standalone \
		--output type=local,dest=$(KYLIN_OUTPUT_DIR) \
		--progress=plain \
		. 2>&1
	@echo ""
	@echo "=== 构建完成 ==="
	@if [ -f $(KYLIN_OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_arm64.deb ]; then \
		echo "成功: $(KYLIN_OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_arm64.deb"; \
		ls -lh $(KYLIN_OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_arm64.deb; \
		sha256sum $(KYLIN_OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_arm64.deb; \
	else \
		echo "警告: DEB 文件可能未生成到 $(KYLIN_OUTPUT_DIR)"; \
		ls -lh $(KYLIN_OUTPUT_DIR)/ 2>/dev/null || true; \
	fi

# 简化别名
build-kylin: build-kylin-arm64

# 清理麒麟构建产物
kylin-clean:
	@echo "=== 清理麒麟 V10 构建产物 ==="
	rm -rf $(KYLIN_OUTPUT_DIR)
	rm -rf backend/dist/assistance-management-backend
	rm -rf backend/build
	docker rmi $(APP_NAME)-kylin:$(VERSION) 2>/dev/null || true
	@echo "清理完成"

# 验证麒麟 DEB 包
kylin-verify:
	@echo "=== 验证麒麟 V10 DEB 包 ==="
	@bash scripts/verify-kylin-deb.sh $(KYLIN_OUTPUT_DIR)/$(APP_NAME)_$(VERSION)_arm64.deb

# 帮助信息
help:
	@echo "帮扶管理信息系统 - Makefile"
	@echo ""
	@echo "可用目标:"
	@echo "  make test         - 运行所有测试（后端 + 前端）"
	@echo "  make test-backend - 运行后端测试"
	@echo "  make test-frontend- 运行前端测试"
	@echo "  make test-e2e     - 运行 E2E 测试"
	@echo "  make coverage     - 生成覆盖率报告"
	@echo "  make deploy-check - 运行部署前检查"
	@echo "  make security     - 运行安全扫描"
	@echo "  make clean        - 清理测试产物"
	@echo "  make install      - 安装所有依赖"
	@echo "  make dev          - 启动开发服务器"
	@echo "  make build        - 构建生产版本"
	@echo "  make electron-build - 打包 Electron 应用"
	@echo "  make win-installer  - 构建 Windows 安装程序"
	@echo ""
	@echo "DEB 包构建（Docker 跨平台，推荐）:"
	@echo "  make build-deb           - 构建 amd64 DEB"
	@echo "  make build-deb-amd64     - 构建 amd64 DEB"
	@echo "  make build-deb-arm64     - 构建 arm64 DEB"
	@echo "  make build-deb-all       - 构建双架构 DEB"
	@echo "  make deb-clean           - 清理 DEB 构建产物"
	@echo ""
	@echo "麒麟 V10 ARM64 单机版（无 Electron）:"
	@echo "  make build-kylin         - 构建麒麟 V10 ARM64 DEB"
	@echo "  make build-kylin-arm64   - 同上"
	@echo "  make kylin-clean         - 清理麒麟构建产物"
	@echo "  make kylin-verify        - 验证麒麟 DEB 包"
	@echo ""
	@echo "示例:"
	@echo "  make build-deb VERSION=1.0.4"
	@echo "  make build-deb-all VERSION=1.0.5"
	@echo ""
	@echo "直接运行构建脚本:"
	@echo "  ./scripts/build-deb.sh amd64      # 构建 amd64"
	@echo "  ./scripts/build-deb.sh arm64      # 构建 arm64"
	@echo "  ./scripts/build-deb.sh all        # 构建双架构"
