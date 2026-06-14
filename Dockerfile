# ============================================================
# 军队乡村振兴管理系统 — 多阶段 Docker 构建 (ARM64)
# 目标: 银河麒麟 V10 (ARM64)
# 输出: .deb 安装包
# ============================================================

# ─── Stage 1: 前端构建 ───
FROM node:20-bookworm AS frontend-builder

RUN npm config set registry https://registry.npmmirror.com && \
    npm config set @sheetjs:registry https://registry.npmmirror.com

WORKDIR /project/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps 2>/dev/null || npm install --legacy-peer-deps --network-timeout=600000

COPY frontend/ ./
RUN npm run build

# ─── Stage 2: 后端 PyInstaller 打包 ───
FROM python:3.11-bookworm AS backend-builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir --timeout 300 -r backend/requirements.txt pyinstaller

COPY backend/ backend/
COPY resources/ resources/
COPY .env.example ./

RUN cd backend && pyinstaller military-rural-backend.spec --clean --noconfirm

RUN mkdir -p dist/backend/linux && \
    cp backend/dist/military-rural-backend dist/backend/linux/military-rural-backend

# ─── Stage 3: Electron 打包 (只生成 .deb) ───
FROM node:20-bookworm AS electron-packager

ENV DEBIAN_FRONTEND=noninteractive
ENV ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/

RUN apt-get update && apt-get install -y --no-install-recommends \
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
    fakeroot \
    dpkg-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

RUN npm config set registry https://registry.npmmirror.com

COPY package.json package-lock.json* ./
RUN npm install --network-timeout=600000

COPY electron/ electron/
COPY resources/ resources/
COPY build/ build/

# 确保图标文件存在且尺寸符合要求（至少 256x256）
RUN mkdir -p resources && \
    if [ ! -f resources/icon.png ]; then \
        convert -size 256x256 xc:blue resources/icon.png; \
    else \
        SIZE=$(identify -format "%w" resources/icon.png) && \
        if [ "$SIZE" -lt 256 ]; then \
            convert resources/icon.png -resize 256x256 resources/icon.png; \
        fi \
    fi

COPY --from=frontend-builder /project/frontend/dist/ frontend/dist/
COPY --from=backend-builder /project/dist/backend/ dist/backend/

ARG VERSION=1.2.0
ARG ARCH=arm64

RUN npx electron-builder --linux deb --${ARCH} --publish never

RUN mkdir -p /output && \
    find . -name "*.deb" -exec cp {} /output/ \; && \
    echo "✅ Debian packages copied to /output"

VOLUME ["/output"]