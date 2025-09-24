from flask import Flask
from flask_cors import CORS
from app.routes import register_routes  # legacy (will be deprecated after phase migration)
from app.api import register_all  # new blueprint aggregated registration
from app.api.response import register_error_handlers
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
    
    # 注册所有API路由（Phase1：并存旧 routes 与新拆分蓝图，确保兼容）
    try:
        register_all(app)  # new modular blueprints
    except Exception as e:
        app.logger.warning(f"新蓝图注册失败，回退旧路由: {e}")
    register_routes(app)  # keep legacy endpoints (duplicate definitions benign if identical)
    # 统一错误处理 (Phase 3)
    register_error_handlers(app)
    return app
