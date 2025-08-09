import os

class Config:
    """基础配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev')
    
    # 数据库配置
    MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT', 27017))
    MONGODB_DB = os.environ.get('MONGODB_DB', 'medc_annotation')
    
    # 静态文件配置
    STATIC_FOLDER = os.environ.get('STATIC_FOLDER', '../static')
    
    # 服务器配置
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 在生产环境中应使用更强的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(24).hex())

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}