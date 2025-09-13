#!/bin/bash

# 医学图像标注系统一键导出离线部署包
# 用于将当前系统打包为完整的离线部署包

set -e  # 遇到错误时退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 医学图像标注系统离线部署包生成 ===${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi

# 检查镜像是否存在
echo -e "${YELLOW}检查本地镜像...${NC}"
if ! docker images | grep -q "yfsdk/medc-backend"; then
    echo -e "${RED}错误: 未找到后端镜像 yfsdk/medc-backend${NC}"
    echo "请先运行 docker-deploy.sh 构建镜像"
    exit 1
fi

if ! docker images | grep -q "yfsdk/medc-frontend"; then
    echo -e "${RED}错误: 未找到前端镜像 yfsdk/medc-frontend${NC}"
    echo "请先运行 docker-deploy.sh 构建镜像"
    exit 1
fi

# 清理旧文件
echo -e "${YELLOW}清理旧文件...${NC}"
rm -rf deploy-offline
mkdir -p deploy-offline/data

# 复制必要文件
echo -e "${YELLOW}复制配置文件...${NC}"
cp docker-compose.prod.yml deploy-offline/docker-compose.yml
cp backend/.env deploy-offline/ 2>/dev/null || echo -e "${YELLOW}警告: .env 文件不存在${NC}"
cp -r README.md deploy-offline/ 2>/dev/null || true

# 获取当前镜像标签
BACKEND_TAG=$(docker images | grep "yfsdk/medc-backend" | awk '{print $2}' | head -1)
FRONTEND_TAG=$(docker images | grep "yfsdk/medc-frontend" | awk '{print $2}' | head -1)

echo -e "${YELLOW}导出镜像...${NC}"
echo "后端镜像: yfsdk/medc-backend:${BACKEND_TAG}"
echo "前端镜像: yfsdk/medc-frontend:${FRONTEND_TAG}"
echo "数据库镜像: mongo:4.4"

# 导出镜像
docker save mongo:4.4 yfsdk/medc-backend:${BACKEND_TAG} yfsdk/medc-frontend:${FRONTEND_TAG} -o deploy-offline/medc-images.tar
echo "镜像导出完成"

# 创建部署脚本
echo -e "${YELLOW}创建部署脚本...${NC}"
cat > deploy-offline/deploy.sh << 'EOF'
#!/bin/bash

echo "=== 医学图像标注系统离线部署脚本 ==="

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

# 检查镜像文件是否存在
if [ ! -f "medc-images.tar" ]; then
    echo "错误: 未找到镜像文件 medc-images.tar"
    exit 1
fi

# 加载镜像
echo "加载Docker镜像..."
docker load -i medc-images.tar

# 创建必要的目录
mkdir -p ./data/mongodb
mkdir -p ./data/uploads
mkdir -p ./logs

# 启动服务
echo "启动服务..."
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
cat > deploy-offline/README.md << 'EOF'
# 医学图像标注系统离线部署说明

此部署包适用于**无法访问互联网**的环境，包含了所有必要的Docker镜像。

## 快速部署

1. 解压部署包（注意：文件较大，约1GB）：
```bash
tar -xf medc-deploy-offline.tar.gz
cd medc-deploy-offline
```

2. 运行部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

## 手动部署步骤

1. 加载Docker镜像：
```bash
docker load -i medc-images.tar
```

2. 创建必要目录：
```bash
mkdir -p data/mongodb
mkdir -p data/uploads
mkdir -p logs
```

3. 启动服务：
```bash
docker-compose up -d
```

4. 访问系统：
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
chmod +x deploy-offline/deploy.sh

# 创建压缩包
echo -e "${YELLOW}创建部署包...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACKAGE_NAME="medc-deploy-offline_${TIMESTAMP}.tar.gz"
tar -czf ${PACKAGE_NAME} -C deploy-offline .

# 计算大小
SIZE=$(du -h ${PACKAGE_NAME} | cut -f1)

echo -e "${GREEN}✅ 离线部署包已创建: ${PACKAGE_NAME} (${SIZE})${NC}"
echo "包含以下镜像:"
echo "- yfsdk/medc-backend:${BACKEND_TAG}"
echo "- yfsdk/medc-frontend:${FRONTEND_TAG}"
echo "- mongo:4.4"
echo ""
echo "使用方法:"
echo "1. 将 ${PACKAGE_NAME} 复制到目标服务器"
echo "2. 解压: tar -xf ${PACKAGE_NAME}"
echo "3. 运行: ./deploy.sh"
