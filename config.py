import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    
    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'xml'}
    
    # AI服务配置
    AI_SERVICE_CONFIG = {
        'dify_url': os.environ.get('DIFY_URL') or 'https://api.dify.ai',
        'dify_token': os.environ.get('DIFY_TOKEN') or '',
        'mock_mode': os.environ.get('AI_MOCK_MODE', 'true').lower() == 'true',
        'timeout': int(os.environ.get('AI_TIMEOUT') or 30),
        'max_retries': int(os.environ.get('AI_MAX_RETRIES') or 3)
    }
    
    # 会话配置
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT') or 3600)  # 1小时
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    # 开发环境默认启用Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()
    AI_SERVICE_CONFIG['mock_mode'] = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    REDIS_DB = 1  # 使用不同的Redis数据库
    
    # 测试环境强制使用Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()
    AI_SERVICE_CONFIG['mock_mode'] = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境根据环境变量决定是否使用Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}