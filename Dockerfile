# ============================================================
# 军队乡村振兴管理系统 — 多阶段 Docker 构建 (x86_64)
# 用途: 在容器中构建 Linux DEB/AppImage 安装包
# 不是生产运行时镜像（系统是离线桌面应用）
# ============================================================

# ─── Stage 1: 前端构建 ───
FROM node:18-bookworm AS frontend-builder

WORKDIR /project/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

COPY frontend/ ./
RUN npm run build

# ─── Stage 2: 后端 PyInstaller 打包 ───
FROM python:3.11-bookworm AS backend-builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt pyinstaller

COPY backend/ backend/
COPY resources/ resources/
COPY .env.example ./

RUN cd backend && pyinstaller military-rural-backend.spec --clean --noconfirm

# 将构建产物复制到 staging 目录
RUN mkdir -p dist/backend/linux && \
    cp backend/dist/military-rural-backend dist/backend/linux/military-rural-backend

# ─── Stage 3: Electron 打包 ───
FROM node:18-bookworm AS electron-packager

ENV DEBIAN_FRONTEND=noninteractive

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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /project

# 复制 npm 配置
COPY package.json package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

# 复制 Electron 源码
COPY electron/ electron/

# 复制构建资源
COPY resources/ resources/
COPY build/ build/

# 从前端构建阶段复制产物
COPY --from=frontend-builder /project/frontend/dist/ frontend/dist/

# 从后端构建阶段复制产物
COPY --from=backend-builder /project/dist/backend/ dist/backend/

# 运行 electron-builder 生成 DEB 和 AppImage
ARG VERSION=1.2.0
ARG ARCH=x64

RUN npx electron-builder --linux deb appimage --${ARCH}

# 输出在 dist/electron/ 目录
