# ============================================================
# 军队乡村振兴管理系统 — 多阶段 Docker 构建 (ARM64)
# 目标: 银河麒麟 V10 (ARM64)
# 输出: .deb 安装包
# ============================================================

# ─── Stage 1: 前端构建 ───
FROM node:20-bookworm AS frontend-builder

# 配置国内镜像源
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set @sheetjs:registry https://registry.npmmirror.com

WORKDIR /project/frontend

# 复制前端依赖文件
COPY frontend/package.json frontend/package-lock.json* ./

# 安装前端依赖
RUN npm install --legacy-peer-deps --network-timeout=600000 --registry=https://registry.npmmirror.com

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: 后端 PyInstaller 打包 ───
FROM python:3.11-bookworm AS backend-builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 配置 pip 国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

# 复制后端依赖文件
COPY backend/requirements.txt backend/

# 安装 Python 依赖
RUN pip install --no-cache-dir --timeout 300 -r backend/requirements.txt pyinstaller

# 复制后端源码
COPY backend/ backend/
COPY resources/ resources/
COPY .env.example ./

# 打包后端为可执行文件
RUN cd backend && pyinstaller military-rural-backend.spec --clean --noconfirm

# 创建后端目录结构
RUN mkdir -p dist/backend/linux && \
    cp backend/dist/military-rural-backend dist/backend/linux/military-rural-backend

# ─── Stage 3: Electron 打包 (生成 .deb) ───
FROM node:20-bookworm AS electron-packager

ENV DEBIAN_FRONTEND=noninteractive
ENV ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
ENV ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true

# 安装完整的系统依赖（修复 app-builder 执行问题）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    build-essential \
    ca-certificates \
    curl \
    wget \
    # Electron Builder 所需的核心库
    libgtk-3-0 \
    libnotify4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libatspi2.0-0 \
    libuuid1 \
    libsecret-1-0 \
    libasound2 \
    libgbm1 \
    # 打包工具
    fakeroot \
    dpkg-dev \
    # 图片处理
    imagemagick \
    # app-builder 运行时依赖（关键）
    libc6 \
    libstdc++6 \
    libgcc-s1 \
    libgconf-2-4 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libfreetype6 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgl1-mesa-glx \
    libgles2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

# 配置 npm 镜像
RUN npm config set registry https://registry.npmmirror.com

# 复制 Electron 依赖文件
COPY package.json package-lock.json* ./

# 安装 Electron 依赖（使用淘宝镜像和更宽松的配置）
RUN npm install --legacy-peer-deps --network-timeout=1200000 --no-audit --no-fund --registry=https://registry.npmmirror.com

# 复制 Electron 源码
COPY electron/ electron/
COPY resources/ resources/
COPY build/ build/

# 确保图标文件存在且尺寸符合要求（至少 256x256）
RUN mkdir -p resources && \
    if [ ! -f resources/icon.png ]; then \
        convert -size 256x256 xc:blue resources/icon.png; \
    else \
        SIZE=$(identify -format "%w" resources/icon.png 2>/dev/null || echo "0") && \
        if [ "$SIZE" -lt 256 ]; then \
            convert resources/icon.png -resize 256x256 resources/icon.png; \
        fi \
    fi

# 复制前端和后端构建产物
COPY --from=frontend-builder /project/frontend/dist/ frontend/dist/
COPY --from=backend-builder /project/dist/backend/ dist/backend/

# 设置构建参数
ARG VERSION=1.2.0
ARG ARCH=arm64

# 确保 app-builder 有正确的执行权限
RUN chmod +x node_modules/@electron/universal/*.js 2>/dev/null || true

# 清理 npm 缓存释放空间
RUN npm cache clean --force

# 构建 .deb 包
RUN npx electron-builder --linux deb --${ARCH} --publish never

# 创建输出目录并复制 .deb 文件
RUN mkdir -p /output && \
    find . -name "*.deb" -exec cp {} /output/ \; && \
    if [ -d /output ] && [ "$(ls -A /output)" ]; then \
        echo "✅ Debian packages copied to /output"; \
        ls -la /output/; \
    else \
        echo "❌ No .deb files found"; \
        exit 1; \
    fi

# 设置输出卷
VOLUME ["/output"]

# ─── Stage 4: 最终镜像（可选，用于调试）───
FROM scratch AS final
COPY --from=electron-packager /output /output