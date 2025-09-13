#!/usr/bin/env python3
"""
日志配置模块
统一管理应用日志输出，支持文件和控制台双重输出
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class LogConfig:
    """日志配置类"""
    
    def __init__(self, log_dir='/app/logs', log_level='INFO'):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, 'app'), exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, 'access'), exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, 'error'), exist_ok=True)
    
    def setup_logger(self, name='medc-app'):
        """设置日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 应用日志文件处理器（轮转）
        app_log_file = os.path.join(self.log_dir, 'app', f'app_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            app_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 错误日志文件处理器
        error_log_file = os.path.join(self.log_dir, 'error', f'error_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        return logger
    
    def setup_access_logger(self):
        """设置访问日志记录器"""
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        access_logger.handlers.clear()
        
        # 访问日志格式
        access_formatter = logging.Formatter(
            '%(asctime)s - %(remote_addr)s - "%(method)s %(url)s %(protocol)s" '
            '%(status_code)s %(response_size)s "%(user_agent)s"'
        )
        
        # 访问日志文件处理器
        access_log_file = os.path.join(self.log_dir, 'access', f'access_{datetime.now().strftime("%Y%m%d")}.log')
        access_handler = RotatingFileHandler(
            access_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        
        return access_logger

# 全局日志配置实例
log_config = LogConfig(
    log_dir=os.getenv('LOG_DIR', '/app/logs'),
    log_level=os.getenv('LOG_LEVEL', 'INFO')
)

# 获取应用日志记录器
app_logger = log_config.setup_logger('medc-app')
access_logger = log_config.setup_access_logger()

def get_logger(name=None):
    """获取日志记录器"""
    if name:
        return logging.getLogger(name)
    return app_logger

def log_request(request, response):
    """记录HTTP请求"""
    access_logger.info('', extra={
        'remote_addr': request.remote_addr,
        'method': request.method,
        'url': request.url,
        'protocol': request.environ.get('SERVER_PROTOCOL'),
        'status_code': response.status_code,
        'response_size': response.content_length or 0,
        'user_agent': request.headers.get('User-Agent', '')
    })
