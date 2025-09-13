#!/bin/bash

# 静态文件部署脚本（不依赖Docker）
echo "=== 前端静态文件部署脚本 ==="

# 检查是否在正确的目录
if [ ! -f "package.json" ]; then
    echo "错误: 请在前端目录运行此脚本"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "安装依赖包..."
    npm install --registry=https://registry.npmmirror.com
fi

# 构建项目
echo "构建前端项目..."
npm run build

# 检查构建是否成功
if [ ! -d "dist" ]; then
    echo "错误: 构建失败，dist目录不存在"
    exit 1
fi

echo "✅ 构建完成"

# 创建部署包
DEPLOY_DIR="../frontend_deploy"
echo "创建部署包到: ${DEPLOY_DIR}"

# 清理并创建部署目录
rm -rf "${DEPLOY_DIR}"
mkdir -p "${DEPLOY_DIR}"

# 复制构建文件
cp -r dist/* "${DEPLOY_DIR}/"
cp nginx.conf "${DEPLOY_DIR}/"

# 创建简单的启动脚本
cat > "${DEPLOY_DIR}/start_server.sh" << 'EOF'
#!/bin/bash
echo "启动前端服务器..."
echo "访问地址: http://localhost:8080"
echo "按Ctrl+C停止服务器"
python3 -m http.server 8080
EOF

chmod +x "${DEPLOY_DIR}/start_server.sh"

echo "✅ 部署包创建完成: ${DEPLOY_DIR}"
echo ""
echo "部署方式:"
echo "1. 本地测试: cd ${DEPLOY_DIR} && ./start_server.sh"
echo "2. 复制 ${DEPLOY_DIR} 目录到服务器"
echo "3. 在服务器上运行: ./start_server.sh"
echo "4. 或者配置nginx指向该目录"
