#!/bin/bash

# 快速测试脚本
# 使用开发环境配置启动服务并测试新功能

set -e

echo "🚀 启动开发环境测试..."

# 1. 检查依赖
echo "📋 检查Python依赖..."
cd /home/droot/medc-img-annotation-app/backend
if [ ! -f requirements.txt ]; then
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 2. 启动后端服务 (后台)
echo "🔧 启动后端服务..."
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 3. 测试新功能
echo "🧪 测试用户独立进度功能..."
python test_user_independent_progress.py

# 4. 清理
echo "🧹 清理服务..."
if ps -p $BACKEND_PID > /dev/null; then
    kill $BACKEND_PID
    echo "✅ 后端服务已停止"
fi

echo "✅ 测试完成！"