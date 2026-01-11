#!/usr/bin/env python3
"""
测试真实的Dify连接
"""

import asyncio
import json
import logging
import aiohttp
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dify_connection():
    """测试Dify连接"""
    print("🔗 测试Dify连接...")
    
    config = Config.AI_SERVICE_CONFIG
    dify_url = config['dify_url']
    dify_token = config['dify_token']
    
    print(f"📋 配置信息:")
    print(f"  DIFY_URL: {dify_url}")
    print(f"  DIFY_TOKEN: {dify_token[:20]}...")
    print(f"  MOCK_MODE: {config['mock_mode']}")
    
    # 测试基本连接
    headers = {
        'Authorization': f'Bearer {dify_token}',
        'Content-Type': 'application/json'
    }
    
    test_message = {
        'inputs': {},
        'query': '测试连接',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🚀 发送测试请求到Dify...")
            
            async with session.post(
                f'{dify_url}/chat-messages',
                json=test_message,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                print(f"📊 响应状态: {response.status}")
                print(f"📊 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Dify连接成功!")
                    print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Dify连接失败: {response.status}")
                    print(f"📝 错误内容: {error_text}")
                    return False
                    
    except aiohttp.ClientTimeout as e:
        print(f"❌ Dify连接超时: {e}")
        return False
    except aiohttp.ClientError as e:
        print(f"❌ Dify连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ai_service_initialization():
    """测试AI服务初始化"""
    print("\n🤖 测试AI服务初始化...")
    
    try:
        from services.ai_service import AIService
        
        # 使用真实配置初始化
        config = Config.AI_SERVICE_CONFIG.copy()
        print(f"📋 初始化配置: mock_mode={config['mock_mode']}")
        
        ai_service = AIService(config)
        
        print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
        print(f"📊 是否Mock模式: {ai_service.mode_selector.is_mock_mode()}")
        
        # 测试一个简单的对话
        session_id = 'test_real_dify'
        message = '你好，这是一个测试消息'
        context = {}
        
        print("🚀 发送测试消息...")
        result = await ai_service.chat_with_agent(session_id, message, context)
        
        print(f"📝 响应结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 检查是否切换到了Mock模式
        final_mode = ai_service.mode_selector.current_mode
        print(f"📊 最终模式: {final_mode}")
        
        if final_mode == 'mock':
            print("⚠️ 系统切换到了Mock模式，可能是Dify连接失败")
            return False
        else:
            print("✅ 系统保持在Dify模式")
            return True
            
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试真实Dify连接")
    print("=" * 60)
    
    # 1. 测试直接的Dify连接
    dify_connection_ok = await test_dify_connection()
    
    # 2. 测试AI服务初始化和使用
    ai_service_ok = await test_ai_service_initialization()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 直接Dify连接: {'成功' if dify_connection_ok else '失败'}")
    print(f"✅ AI服务Dify模式: {'成功' if ai_service_ok else '失败'}")
    
    if not dify_connection_ok:
        print("\n❌ 问题诊断:")
        print("1. 检查网络连接和代理设置")
        print("2. 验证DIFY_TOKEN是否正确")
        print("3. 确认Dify服务是否可用")
    
    if not ai_service_ok:
        print("\n❌ AI服务问题:")
        print("1. 系统自动切换到Mock模式")
        print("2. 需要解决Dify连接问题")

if __name__ == "__main__":
    asyncio.run(main())