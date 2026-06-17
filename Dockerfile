# ============================================================
# Dockerfile - 帮扶管理信息系统
# 适用于: Windows Docker Desktop + ARM64 交叉编译
# ============================================================

# ============================================================
# 阶段 1: 构建前端 (Node.js 18)
# ============================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 设置 npm 镜像加速（解决网络问题）
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY frontend/package*.json ./

# 安装依赖（使用 legacy-peer-deps 解决版本冲突）
RUN npm install --legacy-peer-deps

# 复制源码并构建
COPY frontend/ ./
RUN npm run build

# ============================================================
# 阶段 2: 构建后端 (Python 3.11 + PyInstaller)
# ============================================================
FROM python:3.11-alpine AS backend-builder

WORKDIR /app/backend

# 安装构建依赖
RUN apk add --no-cache \
    gcc \
    g++ \
    make \
    libffi-dev \
    musl-dev \
    linux-headers

# 复制依赖文件
COPY backend/requirements.txt ./

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install pyinstaller

# 复制源码
COPY backend/ ./

# 使用 PyInstaller 打包
RUN pyinstaller --name=assistance-backend \
    --onefile \
    --add-data "app:app" \
    --add-data "alembic:alembic" \
    --add-data "alembic.ini:." \
    --hidden-import=uvicorn \
    --hidden-import=sqlalchemy \
    --hidden-import=alembic \
    --hidden-import=bcrypt \
    --hidden-import=passlib \
    --hidden-import=python_jose \
    --hidden-import=multipart \
    --hidden-import=contourpy \
    start.py

# ============================================================
# 阶段 3: 构建 Electron (ARM64 DEB 包)
# ============================================================
FROM node:18-alpine AS electron-builder

# 安装 Electron 构建依赖
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    libx11-dev \
    libxkbfile-dev \
    libsecret-dev \
    alpine-sdk

WORKDIR /app/electron

# 设置 npm 镜像加速
RUN npm config set registry https://registry.npmmirror.com

# 复制依赖文件
COPY electron/package*.json ./

# 删除 lock 文件，重新安装
RUN rm -f package-lock.json && \
    npm install --legacy-peer-deps

# 安装 electron-builder
RUN npm install -g electron-builder

# 复制源码
COPY electron/ ./

# 构建 ARM64 DEB 包
RUN npx electron-builder --linux --arm64 --deb || true

# ============================================================
# 阶段 4: 组装最终运行镜像
# ============================================================
FROM python:3.11-alpine AS runtime

WORKDIR /app

# 安装运行依赖
RUN apk add --no-cache \
    nodejs \
    npm \
    bash \
    curl \
    libxcb \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libxkbcommon \
    libgtk-3 \
    libnotify \
    nss \
    xdg-utils

# 安装 Python 运行时依赖
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn sqlalchemy alembic bcrypt \
    python-jose[cryptography] passlib[bcrypt] python-multipart \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 serve
RUN npm install -g serve

# 复制后端二进制
COPY --from=backend-builder /app/backend/dist/assistance-backend /app/backend/
RUN chmod +x /app/backend/assistance-backend

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/

# 复制 Electron 构建产物
COPY --from=electron-builder /app/electron/dist/*.deb /app/electron-dist/ 2>/dev/null || true

# 创建启动脚本
RUN cat > /app/start-services.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  帮扶管理信息系统 v1.2.0"
echo "  正在启动服务..."
echo "=========================================="

# 启动后端
echo "启动后端服务..."
"$SCRIPT_DIR/backend/assistance-backend" &
BACKEND_PID=$!

sleep 3

# 启动前端
echo "启动前端服务..."
cd "$SCRIPT_DIR/frontend"
serve -s . -l 3000 &
FRONTEND_PID=$!

echo "=========================================="
echo "服务已启动！"
echo "前端地址: http://localhost:3000"
echo "后端地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "默认账号: admin / admin123"
echo "=========================================="
echo "按 Ctrl+C 停止所有服务"

wait $BACKEND_PID $FRONTEND_PID
EOF

RUN chmod +x /app/start-services.sh

# 暴露端口
EXPOSE 8000 3000

# 启动命令
CMD ["/app/start-services.sh"]