#!/usr/bin/env python3
"""
系统配置文件
统一管理数据库连接、文件路径等配置参数
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGODB_DB', 'medical_annotation')

# 文件上传配置
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'app/static/img')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

# Flask配置
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# 安全配置
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# 打印配置信息（仅在开发模式下）
if FLASK_DEBUG:
    print(f"🔧 配置加载完成:")
    print(f"   数据库: {MONGO_URI}")
    print(f"   数据库名: {MONGO_DB}")
    print(f"   上传目录: {UPLOAD_FOLDER}")
    print(f"   Flask端口: {FLASK_PORT}")
