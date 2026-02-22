import os
import logging
from datetime import datetime

class Logger:
    def __init__(self, name, log_dir=None, is_plugin=False, plugin_name=None):
        """
        初始化日志记录器
        :param name: 日志记录器名称
        :param log_dir: 日志文件存储目录，默认在项目根目录的logs文件夹
        :param is_plugin: 是否为插件日志
        :param plugin_name: 插件名称，当is_plugin为True时必填
        """
        # 优先从环境变量获取日志目录
        env_log_dir = os.getenv('LOG_DIR')
        
        # 如果没有指定日志目录，使用默认目录
        if log_dir is None:
            if env_log_dir:
                self.log_dir = env_log_dir
            else:
                # 获取当前文件所在目录的父目录，即backend目录
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.log_dir = os.path.join(backend_dir, 'logs')
        else:
            self.log_dir = log_dir
        
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 确保插件日志目录存在
        if is_plugin and plugin_name:
            plugin_log_dir = os.path.join(self.log_dir, 'plugins', plugin_name)
            if not os.path.exists(plugin_log_dir):
                os.makedirs(plugin_log_dir)
        
        # 获取当前日期，用于日志文件名
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器，避免重复
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 创建总日志文件处理器（所有日志都会记录到这里）
        all_log_file = os.path.join(self.log_dir, f'all-{current_date}.log')
        all_file_handler = logging.FileHandler(all_log_file, encoding='utf-8')
        all_file_handler.setLevel(logging.DEBUG)
        
        # 创建特定日志文件处理器
        if is_plugin and plugin_name:
            plugin_log_file = os.path.join(self.log_dir, 'plugins', plugin_name, f'{plugin_name}-{current_date}.log')
            specific_file_handler = logging.FileHandler(plugin_log_file, encoding='utf-8')
        else:
            specific_log_file = os.path.join(self.log_dir, f'{name}-{current_date}.log')
            specific_file_handler = logging.FileHandler(specific_log_file, encoding='utf-8')
        
        specific_file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器，用于输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 定义日志格式
        if is_plugin and plugin_name:
            formatter = logging.Formatter('%(asctime)s - [PLUGIN] %(name)s - %(levelname)s - %(message)s')
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        all_file_handler.setFormatter(formatter)
        specific_file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        self.logger.addHandler(all_file_handler)
        self.logger.addHandler(specific_file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """
        输出debug级别的日志
        :param message: 日志消息
        """
        self.logger.debug(message)
    
    def info(self, message):
        """
        输出info级别的日志
        :param message: 日志消息
        """
        self.logger.info(message)
    
    def warning(self, message):
        """
        输出warning级别的日志
        :param message: 日志消息
        """
        self.logger.warning(message)
    
    def error(self, message):
        """
        输出error级别的日志
        :param message: 日志消息
        """
        self.logger.error(message)
    
    def critical(self, message):
        """
        输出critical级别的日志
        :param message: 日志消息
        """
        self.logger.critical(message)

# 创建默认的日志记录器实例
logger = Logger(__name__)

# 创建插件日志记录器的工厂函数
def get_plugin_logger(plugin_name):
    """
    获取插件日志记录器
    :param plugin_name: 插件名称
    :return: 日志记录器实例
    """
    return Logger(f'plugin.{plugin_name}', is_plugin=True, plugin_name=plugin_name)
