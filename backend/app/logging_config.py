import logging
import logging.handlers
import os
from datetime import datetime

class LogConfig:
    """日志配置类 - 统一管理应用日志"""
    
    def __init__(self, log_dir="logs", app_name="medc-backend"):
        self.log_dir = log_dir
        self.app_name = app_name
        self.setup_log_directory()
        
    def setup_log_directory(self):
        """创建日志目录结构"""
        log_dirs = [
            os.path.join(self.log_dir, "app"),
            os.path.join(self.log_dir, "access"), 
            os.path.join(self.log_dir, "error"),
            os.path.join(self.log_dir, "debug")
        ]
        
        for log_dir in log_dirs:
            os.makedirs(log_dir, exist_ok=True)
    
    def get_logger(self, name="main", level=logging.INFO):
        """获取配置好的logger实例"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 文件格式化器
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台格式化器（简化）
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 应用日志文件处理器（按日期轮转）
        app_log_file = os.path.join(self.log_dir, "app", f"{self.app_name}.log")
        file_handler = logging.handlers.TimedRotatingFileHandler(
            app_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        
        # 错误日志文件处理器
        error_log_file = os.path.join(self.log_dir, "error", f"{self.app_name}_error.log")
        error_handler = logging.handlers.TimedRotatingFileHandler(
            error_log_file,
            when='midnight', 
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # 调试日志文件处理器
        debug_log_file = os.path.join(self.log_dir, "debug", f"{self.app_name}_debug.log")
        debug_handler = logging.handlers.TimedRotatingFileHandler(
            debug_log_file,
            when='midnight',
            interval=1, 
            backupCount=7,  # 调试日志保留7天
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(error_handler) 
        logger.addHandler(debug_handler)
        logger.addHandler(console_handler)
        
        return logger

    def get_access_logger(self):
        """获取访问日志记录器"""
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        
        if access_logger.handlers:
            return access_logger
            
        # 访问日志格式
        access_formatter = logging.Formatter(
            fmt='%(asctime)s - %(remote_addr)s - "%(method)s %(url)s %(protocol)s" %(status_code)s %(content_length)s "%(user_agent)s"',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 访问日志文件处理器
        access_log_file = os.path.join(self.log_dir, "access", "access.log")
        access_handler = logging.handlers.TimedRotatingFileHandler(
            access_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(access_formatter)
        
        access_logger.addHandler(access_handler)
        return access_logger

# 全局日志配置实例
log_config = LogConfig()

# 便捷函数
def get_logger(name="main"):
    """快速获取logger"""
    return log_config.get_logger(name)

def get_access_logger():
    """快速获取访问logger"""
    return log_config.get_access_logger()

# 使用示例
if __name__ == "__main__":
    # 测试日志配置
    logger = get_logger("test")
    access_logger = get_access_logger()
    
    logger.info("应用启动")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.debug("这是调试信息")
    
    print("日志配置测试完成，请检查 logs/ 目录")
