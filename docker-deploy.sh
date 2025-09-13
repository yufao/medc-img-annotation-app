#!/bin/bash

# 医学图像标注系统 Docker 部署脚本
# 用途：自动化构建、推送和部署流程

set -e  # 遇到错误时退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置参数
DOCKER_USERNAME="yfsdk"
PROJECT_NAME="medc-img-annotation-app"
BACKEND_IMAGE="${DOCKER_USERNAME}/medc-backend"
FRONTEND_IMAGE="${DOCKER_USERNAME}/medc-frontend"
TAG="latest"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未在PATH中"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装或未在PATH中"
        exit 1
    fi
    
    # 检查Docker权限
    if ! docker info &> /dev/null; then
        log_error "Docker权限不足，请运行: sudo usermod -aG docker $USER"
        exit 1
    fi
    
    log_info "依赖检查完成 ✓"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p data/{images,annotations,datasets}
    mkdir -p logs/{app,mongodb,nginx,access}
    mkdir -p static/img
    
    # 如果存在现有图片，迁移到新结构
    if [ -d "backend/app/static/img" ] && [ "$(ls -A backend/app/static/img)" ]; then
        log_info "迁移现有图片到新目录结构..."
        cp -r backend/app/static/img/* static/img/ 2>/dev/null || true
        log_info "图片迁移完成: $(ls static/img/ | wc -l) 个文件"
    fi
    
    # 设置权限
    chmod -R 755 data logs static
    
    log_info "目录结构创建完成 ✓"
}

# 构建镜像
build_images() {
    log_info "开始构建Docker镜像..."
    
    # 清理构建缓存
    docker builder prune -f
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    docker build -t ${BACKEND_IMAGE}:${TAG} ./backend
    
    # 构建前端镜像  
    log_info "构建前端镜像..."
    docker build -t ${FRONTEND_IMAGE}:${TAG} ./frontend
    
    # 显示镜像信息
    docker images | grep medc
    
    log_info "镜像构建完成 ✓"
}

# 推送镜像
push_images() {
    log_info "推送镜像到Docker Hub..."
    
    # 检查是否已登录
    if ! docker info | grep -q "Username:"; then
        log_warn "未登录Docker Hub，请先登录..."
        docker login
    fi
    
    # 推送镜像
    docker push ${BACKEND_IMAGE}:${TAG}
    docker push ${FRONTEND_IMAGE}:${TAG}
    
    log_info "镜像推送完成 ✓"
}

# 本地测试
test_local() {
    log_info "启动本地测试..."
    
    # 停止现有容器
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动（30秒）..."
    sleep 30
    
    # 检查服务状态
    docker-compose ps
    
    # 测试API连接
    if curl -f http://localhost:5000/health &>/dev/null; then
        log_info "后端服务测试通过 ✓"
    else
        log_warn "后端服务测试失败，请检查日志"
        docker-compose logs backend
    fi
    
    # 测试前端连接
    if curl -f http://localhost/ &>/dev/null; then
        log_info "前端服务测试通过 ✓"
    else
        log_warn "前端服务测试失败，请检查日志"
        docker-compose logs frontend
    fi
}

# 生成部署包
generate_deployment_package() {
    log_info "生成部署包..."
    
    PACKAGE_NAME="${PROJECT_NAME}-deployment-$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # 创建临时目录
    TEMP_DIR="/tmp/${PROJECT_NAME}-deploy"
    rm -rf ${TEMP_DIR}
    mkdir -p ${TEMP_DIR}
    
    # 复制部署文件
    cp docker-compose.prod.yml ${TEMP_DIR}/docker-compose.yml
    cp docker-deploy.sh ${TEMP_DIR}/
    
    # 复制数据（如果需要）
    if [ -d "static/img" ] && [ "$(ls -A static/img)" ]; then
        mkdir -p ${TEMP_DIR}/static/img
        cp -r static/img/* ${TEMP_DIR}/static/img/
    fi
    
    # 创建README
    cat > ${TEMP_DIR}/README.md << EOF
# 医学图像标注系统部署包

## 快速部署

1. 解压部署包
2. 安装Docker和Docker Compose
3. 运行部署脚本：
   \`\`\`bash
   chmod +x docker-deploy.sh
   ./docker-deploy.sh
   \`\`\`

## 访问地址

- 前端应用: http://localhost/
- 后端API: http://localhost:5000/
- API文档: http://localhost:5000/doc

## 目录结构

- data/: 数据存储目录
- logs/: 日志文件目录  
- static/: 静态文件目录

EOF
    
    # 打包
    cd /tmp
    tar -czf ${PACKAGE_NAME} ${PROJECT_NAME}-deploy/
    mv ${PACKAGE_NAME} $(dirname $0)/
    rm -rf ${TEMP_DIR}
    
    log_info "部署包生成完成: ${PACKAGE_NAME} ✓"
}

# 显示使用帮助
show_help() {
    echo "医学图像标注系统 Docker 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     构建Docker镜像"
    echo "  push      推送镜像到Docker Hub"
    echo "  test      本地测试"
    echo "  package   生成部署包"
    echo "  deploy    完整部署流程（构建+推送+测试）"
    echo "  help      显示此帮助信息"
    echo ""
}

# 主流程
main() {
    case "${1:-help}" in
        "build")
            check_dependencies
            create_directories
            build_images
            ;;
        "push")
            check_dependencies
            push_images
            ;;
        "test")
            check_dependencies
            test_local
            ;;
        "package")
            generate_deployment_package
            ;;
        "deploy")
            check_dependencies
            create_directories
            build_images
            push_images
            test_local
            generate_deployment_package
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 脚本入口
main "$@"
