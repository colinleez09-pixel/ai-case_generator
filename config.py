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
        'dify_url': os.environ.get('DIFY_URL') or 'https://api.dify.ai/v1',
        'dify_token': os.environ.get('DIFY_TOKEN') or 'app-t1zb7O8HHO3GaHOSOhaDygJ5',
        'mock_mode': os.environ.get('AI_MOCK_MODE', 'true').lower() == 'true',
        'timeout': int(os.environ.get('AI_TIMEOUT') or 30),
        'max_retries': int(os.environ.get('AI_MAX_RETRIES') or 3),
        'stream_mode': os.environ.get('DIFY_STREAM_MODE', 'true').lower() == 'true',
        
        # 错误处理配置
        'error_handling': {
            'base_delay': float(os.environ.get('AI_RETRY_BASE_DELAY') or 1.0),
            'max_delay': float(os.environ.get('AI_RETRY_MAX_DELAY') or 30.0),
            'exponential_base': float(os.environ.get('AI_RETRY_EXPONENTIAL_BASE') or 2.0),
            'client_error_fallback': os.environ.get('AI_CLIENT_ERROR_FALLBACK', 'true').lower() == 'true'
        },
        
        # 熔断器配置
        'circuit_breaker_failure_threshold': int(os.environ.get('AI_CIRCUIT_BREAKER_FAILURE_THRESHOLD') or 5),
        'circuit_breaker_timeout': int(os.environ.get('AI_CIRCUIT_BREAKER_TIMEOUT') or 60),
        'circuit_breaker_success_threshold': int(os.environ.get('AI_CIRCUIT_BREAKER_SUCCESS_THRESHOLD') or 3)
    }
    
    # 测试数据配置
    TEST_DATA_CONFIG = {
        'default_test_case': """
测试场景：用户登录功能测试
测试目标：验证用户能够成功登录系统
前置条件：用户已注册账号
测试步骤：
1. 打开登录页面
2. 输入用户名和密码
3. 点击登录按钮
预期结果：成功跳转到用户仪表板页面
        """.strip(),
        'scenarios': {
            'login': '用户登录功能测试场景',
            'search': '搜索功能测试场景',
            'order': '订单处理测试场景',
            'payment': '支付流程测试场景',
            'profile': '用户资料管理测试场景'
        }
    }
    
    # 会话配置
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT') or 3600)  # 1小时
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    # 开发环境使用环境变量配置，不强制覆盖Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()
    AI_SERVICE_CONFIG['test_data_config'] = Config.TEST_DATA_CONFIG

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    REDIS_DB = 1  # 使用不同的Redis数据库
    
    # 测试环境强制使用Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()
    AI_SERVICE_CONFIG['mock_mode'] = True
    AI_SERVICE_CONFIG['test_data_config'] = Config.TEST_DATA_CONFIG

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境根据环境变量决定是否使用Mock模式
    AI_SERVICE_CONFIG = Config.AI_SERVICE_CONFIG.copy()
    AI_SERVICE_CONFIG['test_data_config'] = Config.TEST_DATA_CONFIG

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}