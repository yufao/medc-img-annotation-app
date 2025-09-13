import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime

class Logger:
    """统一日志处理类"""
    
    def __init__(self, app_name="medc-img-annotation"):
        self.app_name = app_name
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 创建日志对象
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除之前的处理器，避免重复
        if self.logger.handlers:
            self.logger.handlers = []
        
        # 设置环境
        self.env = os.getenv("ENV", "development")
        
        # 设置格式化器
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG if self.env == "development" else logging.INFO)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器（一般日志）
        log_file = os.path.join(self.log_dir, f"{app_name}.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # 添加错误日志文件处理器
        error_log_file = os.path.join(self.log_dir, f"{app_name}_error.log")
        error_file_handler = RotatingFileHandler(
            error_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        error_file_handler.setFormatter(formatter)
        error_file_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_file_handler)
    
    def get_logger(self):
        """获取日志记录器"""
        return self.logger

# 创建全局日志实例
logger = Logger().get_logger()
