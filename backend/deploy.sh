#!/bin/bash

# 设置环境变量
export FLASK_ENV=production
export MONGODB_HOST=localhost  # 改为实际的MongoDB服务器地址
export MONGODB_PORT=27017
export MONGODB_DB=medc_annotation
export SECRET_KEY=$(openssl rand -hex 24)
export JWT_SECRET_KEY=$(openssl rand -hex 24)
export STATIC_FOLDER="../static"

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 确保requirements.txt中包含gunicorn
if ! grep -q "gunicorn" requirements.txt; then
    echo "Adding gunicorn to requirements..."
    echo "gunicorn==20.1.0" >> requirements.txt
    pip install gunicorn==20.1.0
fi

# 启动应用
echo "Starting application with Gunicorn..."
gunicorn --bind 0.0.0.0:5000 wsgi:app --workers 4 --timeout 120