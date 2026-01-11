#!/usr/bin/env python3
"""
测试配置加载是否正确
"""

import os
from dotenv import load_dotenv
from config import config

# 加载环境变量
load_dotenv()

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    # 检查环境变量
    print(f"环境变量 AI_MOCK_MODE: {os.getenv('AI_MOCK_MODE')}")
    print(f"环境变量 DIFY_URL: {os.getenv('DIFY_URL')}")
    print(f"环境变量 DIFY_TOKEN: {os.getenv('DIFY_TOKEN', '')[:20]}...")
    
    # 检查配置类
    flask_env = os.environ.get('FLASK_ENV', 'default')
    print(f"Flask环境: {flask_env}")
    
    config_class = config[flask_env]
    ai_config = config_class.AI_SERVICE_CONFIG
    
    print(f"配置类: {config_class.__name__}")
    print(f"Mock模式: {ai_config['mock_mode']}")
    print(f"Dify URL: {ai_config['dify_url']}")
    print(f"Dify Token: {ai_config['dify_token'][:20]}...")
    
    # 测试AI服务初始化
    print("\n=== 测试AI服务初始化 ===")
    from services.ai_service import AIService
    
    ai_service = AIService(ai_config)
    print(f"AI服务模式: {ai_service.mode_selector.current_mode}")
    print(f"Mock模式状态: {ai_service.mode_selector.is_mock_mode()}")
    
    # 健康检查
    health = ai_service.health_check()
    print(f"健康状态: {health['status']}")
    print(f"运行模式: {health['mode']}")
    
    if health['mode'] == 'dify':
        print("✅ 成功！Dify模式已启用")
        return True
    else:
        print("❌ 失败！仍在Mock模式")
        return False

if __name__ == "__main__":
    success = test_config_loading()
    exit(0 if success else 1)