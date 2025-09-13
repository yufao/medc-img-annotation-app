#!/bin/bash

# 医学图像标注系统管理脚本
# 提供系统的启动、停止、构建、部署等功能

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="医学图像标注系统"
DOCKER_USERNAME="yfsdk"
BACKEND_IMAGE="${DOCKER_USERNAME}/medc-backend"
FRONTEND_IMAGE="${DOCKER_USERNAME}/medc-frontend"

# 显示帮助信息
show_help() {
    echo -e "${BLUE}${PROJECT_NAME} 管理脚本${NC}"
    echo
    echo "用法: $0 [命令] [选项]"
    echo
    echo "🚀 基本操作:"
    echo "  start          启动系统"
    echo "  stop           停止系统"
    echo "  restart        重启系统"
    echo "  status         查看运行状态"
    echo "  logs           查看日志"
    echo
    echo "🔧 开发操作:"
    echo "  dev            启动开发环境"
    echo "  build          构建Docker镜像"
    echo "  test           运行测试"
    echo
    echo "📦 部署操作:"
    echo "  deploy         生产环境部署"
    echo "  package        创建部署包"
    echo "  clean          清理环境"
    echo
    echo "📖 其他:"
    echo "  setup          初始化环境"
    echo "  help           显示帮助信息"
    echo
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查系统依赖...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
    
    # 检查Docker权限
    if ! docker info &> /dev/null; then
        echo -e "${RED}错误: Docker权限不足${NC}"
        echo "请运行: sudo usermod -aG docker \$USER && newgrp docker"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查完成${NC}"
}

# 初始化环境
setup_environment() {
    echo -e "${YELLOW}初始化环境...${NC}"
    
    # 创建必要目录
    mkdir -p data/{mongodb,uploads} logs static/img
    
    # 迁移现有图片
    if [ -d "backend/app/static/img" ] && [ "$(ls -A backend/app/static/img 2>/dev/null)" ]; then
        echo "迁移现有图片..."
        cp -r backend/app/static/img/* static/img/ 2>/dev/null || true
        echo "✅ 图片迁移完成"
    fi
    
    # 创建环境配置
    if [ ! -f "backend/.env" ]; then
        echo "创建环境配置..."
        cat > backend/.env << EOF
MONGODB_URI=mongodb://mongodb:27017/medcimgdb
MONGODB_DB=medcimgdb
UPLOAD_FOLDER=/app/static/img
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=$(openssl rand -hex 24)
JWT_SECRET_KEY=$(openssl rand -hex 24)
EOF
    fi
    
    echo -e "${GREEN}✅ 环境初始化完成${NC}"
}

# 启动开发环境
start_dev() {
    echo -e "${YELLOW}启动开发环境...${NC}"
    setup_environment
    docker-compose up --build
}

# 启动生产环境
start_prod() {
    echo -e "${YELLOW}启动生产环境...${NC}"
    setup_environment
    docker-compose -f docker-compose.prod.yml up -d
    show_access_info
}

# 停止系统
stop_system() {
    echo -e "${YELLOW}停止系统...${NC}"
    docker-compose down
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    echo -e "${GREEN}✅ 系统已停止${NC}"
}

# 重启系统
restart_system() {
    stop_system
    start_prod
}

# 查看状态
show_status() {
    echo -e "${BLUE}系统运行状态:${NC}"
    docker-compose ps
    echo
    echo -e "${BLUE}Docker镜像:${NC}"
    docker images | grep -E "(medc|mongo)" || echo "未找到相关镜像"
}

# 查看日志
show_logs() {
    echo -e "${YELLOW}查看系统日志 (Ctrl+C 退出):${NC}"
    docker-compose logs -f
}

# 构建镜像
build_images() {
    echo -e "${YELLOW}构建Docker镜像...${NC}"
    
    # 构建后端
    echo "构建后端镜像..."
    docker build -t ${BACKEND_IMAGE}:latest ./backend
    
    # 构建前端
    echo "构建前端镜像..."
    docker build -t ${FRONTEND_IMAGE}:v1 ./frontend
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
    docker images | grep medc
}

# 运行测试
run_tests() {
    echo -e "${YELLOW}运行系统测试...${NC}"
    
    # 后端测试
    if [ -f "backend/run_test.sh" ]; then
        echo "运行后端测试..."
        cd backend && bash run_test.sh && cd ..
    fi
    
    echo -e "${GREEN}✅ 测试完成${NC}"
}

# 创建部署包
create_package() {
    echo -e "${YELLOW}选择部署包类型:${NC}"
    echo "1) 在线部署包 (小体积，需要网络)"
    echo "2) 离线部署包 (大体积，包含镜像)"
    read -p "请选择 [1-2]: " choice
    
    case $choice in
        1)
            ./create-online-package.sh
            ;;
        2)
            ./create-offline-package.sh
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            exit 1
            ;;
    esac
}

# 清理环境
clean_environment() {
    echo -e "${YELLOW}清理环境...${NC}"
    read -p "确定要清理所有数据吗？这将删除所有容器、镜像和数据 [y/N]: " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        docker rmi $(docker images | grep medc | awk '{print $3}') 2>/dev/null || true
        rm -rf data logs static
        echo -e "${GREEN}✅ 环境清理完成${NC}"
    else
        echo "已取消"
    fi
}

# 显示访问信息
show_access_info() {
    echo
    echo -e "${GREEN}✅ 系统启动成功!${NC}"
    echo
    echo -e "${BLUE}访问地址:${NC}"
    echo "  🌐 前端界面: http://localhost"
    echo "  🔧 后端API:  http://localhost:5000"
    echo
    echo -e "${BLUE}默认账户:${NC}"
    echo "  👨‍💼 管理员: admin/admin123"
    echo "  👨‍⚕️ 医生:   doctor/doctor123"
    echo "  👨‍🎓 学生:   student/student123"
    echo
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            check_dependencies
            start_prod
            ;;
        stop)
            stop_system
            ;;
        restart)
            check_dependencies
            restart_system
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        dev)
            check_dependencies
            start_dev
            ;;
        build)
            check_dependencies
            build_images
            ;;
        test)
            run_tests
            ;;
        deploy)
            check_dependencies
            start_prod
            ;;
        package)
            check_dependencies
            create_package
            ;;
        setup)
            check_dependencies
            setup_environment
            ;;
        clean)
            clean_environment
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
