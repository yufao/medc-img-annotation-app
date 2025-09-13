#!/bin/bash

# 医学图像标注系统在线部署包生成脚本
# 用于将当前系统打包为可以从Docker Hub拉取镜像的部署包

set -e  # 遇到错误时退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 医学图像标注系统在线部署包生成 ===${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi

# 清理旧文件
echo -e "${YELLOW}清理旧文件...${NC}"
rm -rf deploy-online
mkdir -p deploy-online/data

# 复制必要文件
echo -e "${YELLOW}复制配置文件...${NC}"
cp docker-compose.prod.yml deploy-online/docker-compose.yml
cp backend/.env deploy-online/ 2>/dev/null || echo -e "${YELLOW}警告: .env 文件不存在${NC}"
cp -r README.md deploy-online/ 2>/dev/null || true

# 获取当前镜像标签
BACKEND_TAG=$(docker images | grep "yfsdk/medc-backend" | awk '{print $2}' | head -1)
FRONTEND_TAG=$(docker images | grep "yfsdk/medc-frontend" | awk '{print $2}' | head -1)

# 更新docker-compose.yml中的镜像标签
echo -e "${YELLOW}更新Docker Compose配置...${NC}"
sed -i "s|yfsdk/medc-backend:latest|yfsdk/medc-backend:${BACKEND_TAG}|g" deploy-online/docker-compose.yml
sed -i "s|yfsdk/medc-frontend:latest|yfsdk/medc-frontend:${FRONTEND_TAG}|g" deploy-online/docker-compose.yml

# 确保标签正确
echo "使用的镜像标签:"
echo "- 后端镜像: yfsdk/medc-backend:${BACKEND_TAG}"
echo "- 前端镜像: yfsdk/medc-frontend:${FRONTEND_TAG}"

# 创建部署脚本
echo -e "${YELLOW}创建部署脚本...${NC}"
cat > deploy-online/deploy.sh << 'EOF'
#!/bin/bash

echo "=== 医学图像标注系统在线部署脚本 ==="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
mkdir -p ./data/mongodb
mkdir -p ./data/uploads
mkdir -p ./logs

# 拉取镜像并启动服务
echo "拉取镜像并启动服务..."
docker-compose pull
docker-compose up -d

echo "✅ 服务启动完成!"
echo ""
echo "访问地址:"
echo "  前端: http://localhost"
echo "  后端: http://localhost:5000"
echo ""
echo "默认账户:"
echo "  管理员: admin/admin123"
echo "  医生: doctor/doctor123"
echo "  学生: student/student123"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
EOF

# 添加说明文档
echo -e "${YELLOW}创建说明文档...${NC}"
cat > deploy-online/README.md << 'EOF'
# 医学图像标注系统在线部署说明

此部署包适用于**可访问互联网**的环境，将从Docker Hub下载所需镜像。

## 快速部署

1. 解压部署包：
```bash
tar -xf medc-deploy-online.tar.gz
cd medc-deploy-online
```

2. 运行部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

## 手动部署步骤

1. 创建必要目录：
```bash
mkdir -p data/mongodb
mkdir -p data/uploads
mkdir -p logs
```

2. 拉取镜像并启动服务：
```bash
docker-compose pull
docker-compose up -d
```

3. 访问系统：
- 前端界面：http://localhost
- API服务：http://localhost:5000

## 默认账户
- 管理员：admin/admin123
- 医生：doctor/doctor123
- 学生：student/student123

## 常用命令
- 查看服务状态：`docker-compose ps`
- 查看服务日志：`docker-compose logs -f`
- 停止服务：`docker-compose down`
- 重启服务：`docker-compose restart`
EOF

# 添加可执行权限
chmod +x deploy-online/deploy.sh

# 创建压缩包
echo -e "${YELLOW}创建部署包...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACKAGE_NAME="medc-deploy-online_${TIMESTAMP}.tar.gz"
tar -czf ${PACKAGE_NAME} -C deploy-online .

# 计算大小
SIZE=$(du -h ${PACKAGE_NAME} | cut -f1)

echo -e "${GREEN}✅ 在线部署包已创建: ${PACKAGE_NAME} (${SIZE})${NC}"
echo "需要从Docker Hub拉取的镜像:"
echo "- yfsdk/medc-backend:${BACKEND_TAG}"
echo "- yfsdk/medc-frontend:${FRONTEND_TAG}"
echo "- mongo:4.4"
echo ""
echo "使用方法:"
echo "1. 确保镜像已推送到Docker Hub: docker push yfsdk/medc-backend:${BACKEND_TAG} yfsdk/medc-frontend:${FRONTEND_TAG}"
echo "2. 将 ${PACKAGE_NAME} 复制到目标服务器"
echo "3. 解压: tar -xf ${PACKAGE_NAME}"
echo "4. 运行: ./deploy.sh"
