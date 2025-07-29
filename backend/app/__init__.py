from flask import Flask
from flask_cors import CORS
from app.routes import register_routes
import os

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
    # 注册所有API路由
    register_routes(app)
    return app
