import pytest
import os
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

def test_config_classes():
    """测试配置类的基本属性"""
    # 测试基础配置
    assert hasattr(Config, 'SECRET_KEY')
    assert hasattr(Config, 'REDIS_HOST')
    assert hasattr(Config, 'UPLOAD_FOLDER')
    assert hasattr(Config, 'AI_SERVICE_CONFIG')
    
    # 测试开发配置
    dev_config = DevelopmentConfig()
    assert dev_config.DEBUG == True
    assert dev_config.AI_SERVICE_CONFIG['mock_mode'] == True
    
    # 测试测试配置
    test_config = TestingConfig()
    assert test_config.TESTING == True
    assert test_config.AI_SERVICE_CONFIG['mock_mode'] == True
    assert test_config.REDIS_DB == 1
    
    # 测试生产配置
    prod_config = ProductionConfig()
    assert prod_config.DEBUG == False
    assert 'mock_mode' in prod_config.AI_SERVICE_CONFIG

def test_config_environment_variables():
    """测试环境变量配置"""
    # 保存原始值
    original_secret = os.environ.get('SECRET_KEY')
    original_redis = os.environ.get('REDIS_HOST')
    
    # 设置测试环境变量
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['REDIS_HOST'] = 'test-redis'
    
    # 重新导入配置以获取新的环境变量
    import importlib
    import config
    importlib.reload(config)
    
    test_config = config.Config()
    assert test_config.SECRET_KEY == 'test-secret'
    assert test_config.REDIS_HOST == 'test-redis'
    
    # 恢复原始环境变量
    if original_secret:
        os.environ['SECRET_KEY'] = original_secret
    else:
        os.environ.pop('SECRET_KEY', None)
    
    if original_redis:
        os.environ['REDIS_HOST'] = original_redis
    else:
        os.environ.pop('REDIS_HOST', None)
    
    # 重新加载配置
    importlib.reload(config)

def test_config_defaults():
    """测试默认配置值"""
    config = Config()
    assert config.REDIS_PORT == 6379
    assert config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
    assert 'xml' in config.ALLOWED_EXTENSIONS
    assert config.SESSION_TIMEOUT == 3600