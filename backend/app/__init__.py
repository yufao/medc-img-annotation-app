from flask import Flask
from flask_cors import CORS
from app.routes import register_routes
from app.database_init import init_database
import os
import sys
import logging

# 添加后端目录到系统路径，用于导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO)

# Flask应用工厂，支持自定义静态文件目录
def create_app(static_folder=None):
    # static_folder: 指定静态文件目录，默认'static'，可由run.py传入
    app = Flask(__name__, static_folder=static_folder or 'static')
    CORS(app)
    # 加载密钥配置
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'dev'),
    )
    
    # 初始化数据库结构
    try:
        from config import MONGO_URI, MONGO_DB
        init_database(MONGO_URI, MONGO_DB)
    except Exception as e:
        logging.warning(f"数据库初始化跳过: {e}")
    
    # 注册所有API路由
    register_routes(app)
    return app
