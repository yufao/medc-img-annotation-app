from flask import Flask
from flask_cors import CORS
from app.routes import register_routes
from pymongo import MongoClient
import os
from config import config

# 创建数据库连接
def get_db_connection(config_name='default'):
    """根据配置创建MongoDB连接"""
    cfg = config[config_name]
    client = MongoClient(
        host=cfg.MONGODB_HOST,
        port=cfg.MONGODB_PORT
    )
    return client[cfg.MONGODB_DB]

# Flask应用工厂，支持自定义静态文件目录
def create_app(config_name='default', static_folder=None):
    # 获取配置
    cfg = config[config_name]
    
    # static_folder: 指定静态文件目录，默认使用配置中的值
    app = Flask(__name__, static_folder=static_folder or cfg.STATIC_FOLDER)
    CORS(app)
    
    # 加载配置
    app.config.from_object(cfg)
    
    # 创建数据库连接
    db = get_db_connection(config_name)
    
    # 将db对象添加到g对象中，使其在请求上下文中可用
    @app.before_request
    def before_request():
        from flask import g
        g.db = db
    
    # 注册所有API路由，传入数据库连接
    register_routes(app, db)
    
    return app