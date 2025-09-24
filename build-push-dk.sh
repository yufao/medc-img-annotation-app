#!/bin/bash
# 构建脚本 build-and-push.sh

set -e

echo "🏗️ 开始构建医学图像标注系统镜像..."

# 版本信息
VERSION="v1.2"
DATE=$(date +%Y%m%d_%H%M%S)
TAG="${VERSION}-${DATE}"

# Docker Hub用户名
DOCKER_USERNAME="yfsdk"

# 检查Docker环境
echo "检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

# 设置Docker构建器为传统模式（避免buildx问题）
export DOCKER_BUILDKIT=0

# 1. 构建后端镜像
echo "构建后端镜像..."
docker build --no-cache -t ${DOCKER_USERNAME}/medc-backend:${TAG} ./backend
docker build -t ${DOCKER_USERNAME}/medc-backend:latest ./backend

# 2. 构建前端镜像（使用传统构建方式）
echo "构建前端镜像..."

# 先检查前端是否已构建
if [ ! -d "frontend/dist" ]; then
    echo "前端未构建，正在构建前端..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install --registry=https://registry.npmmirror.com
    fi
    npm run build
    cd ..
fi

# 使用传统Docker构建（不使用buildx）
DOCKER_BUILDKIT=0 docker build --no-cache -t ${DOCKER_USERNAME}/medc-frontend:${TAG} ./frontend
DOCKER_BUILDKIT=0 docker build -t ${DOCKER_USERNAME}/medc-frontend:latest ./frontend

# 3. 验证构建
echo "验证镜像构建..."
docker images | grep medc

# 4. 推送到Docker Hub
echo "推送镜像到Docker Hub..."
docker push ${DOCKER_USERNAME}/medc-backend:${TAG}
docker push ${DOCKER_USERNAME}/medc-backend:latest
docker push ${DOCKER_USERNAME}/medc-frontend:${TAG}
docker push ${DOCKER_USERNAME}/medc-frontend:latest

echo "✅ 镜像构建和推送完成！"
echo "后端镜像: ${DOCKER_USERNAME}/medc-backend:${TAG}"
echo "前端镜像: ${DOCKER_USERNAME}/medc-frontend:${TAG}"