#!/usr/bin/env python3
"""
测试超时场景
"""

import asyncio
import json
import logging
from unittest.mock import patch, AsyncMock
from services.file_service import FileService
from services.session_service import SessionService
from services.generation_service import GenerationService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dify_timeout_scenario():
    """测试Dify超时场景"""
    print("⏰ 测试Dify超时场景...")
    
    try:
        # 1. 初始化服务
        print("📋 初始化服务...")
        file_service = FileService(upload_folder="uploads")
        
        # 创建Mock Redis客户端
        class MockRedisClient:
            def __init__(self):
                self.data = {}
            
            def get(self, key):
                return self.data.get(key)
            
            def set(self, key, value, ex=None):
                self.data[key] = value
                return True
            
            def setex(self, key, time, value):
                self.data[key] = value
                return True
            
            def delete(self, key):
                if key in self.data:
                    del self.data[key]
                return True
            
            def exists(self, key):
                return key in self.data
        
        mock_redis = MockRedisClient()
        session_service = SessionService(mock_redis)
        
        # 使用真实的Dify配置，但Mock网络请求使其超时
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = False  # 使用真实Dify配置
        ai_config['timeout'] = 1  # 设置很短的超时时间
        ai_service = AIService(ai_config)
        
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 2. Mock Dify请求使其抛出超时异常
        async def mock_dify_request(*args, **kwargs):
            import aiohttp
            raise aiohttp.ClientTimeout("Connection timeout")
        
        # 3. 模拟文件上传
        print("📁 模拟文件上传...")
        
        files_info = {
            'case_template': {
                'file_id': 'test_case_template_123',
                'file_path': 'test_case_chinese.xml',
                'original_filename': 'test_case_chinese.xml',
                'file_size': 1024
            }
        }
        
        # 4. 使用patch模拟网络超时
        with patch.object(ai_service, '_dify_chat_request', side_effect=Exception("Connection timeout")):
            print("🤖 测试自动分析和对话（模拟超时）...")
            session_id = 'test_session_timeout'
            
            result = await generation_service.auto_analyze_and_chat(session_id, files_info)
            
            print("✅ 自动分析结果（超时后的降级）:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            return result
        
    except Exception as e:
        print(f"❌ 超时场景测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_chat_with_agent_timeout():
    """直接测试chat_with_agent的超时场景"""
    print("\n🎯 直接测试chat_with_agent的超时场景...")
    
    try:
        # 初始化AIService
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = False  # 使用真实Dify配置
        ai_service = AIService(ai_config)
        
        session_id = 'test_timeout_chat'
        message = """我上传了一个测试用例文件：test_case_chinese.xml

以下是文件中的测试用例内容：

【预置条件】
1. CBS系统运行正常
2. 修改系统变量SYS_abc的值为12
3. 设置变量，初始金额为100

【测试步骤】
1. 进行调账，调减20元

【预期结果】
1. 调账成功
2. account_balance表amount字段值为80

请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"""
        
        context = {
            'user_initiated': True,
            'file_name': 'test_case_chinese.xml'
        }
        
        # 使用patch模拟网络超时
        with patch.object(ai_service, '_dify_chat_request', side_effect=Exception("Connection timeout")):
            result = await ai_service.chat_with_agent(session_id, message, context)
            
            print("✅ chat_with_agent结果（超时后的降级）:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            return result
        
    except Exception as e:
        print(f"❌ chat_with_agent超时测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_mock_response_without_success_field():
    """测试Mock响应缺少success字段的情况"""
    print("\n🧪 测试Mock响应缺少success字段的情况...")
    
    try:
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True
        ai_service = AIService(ai_config)
        
        # 测试不同的消息，看看是否所有情况都返回success字段
        test_messages = [
            "普通消息",
            "我上传了一个测试用例文件：test.xml\n\n以下是文件中的测试用例内容：\n\n【预置条件】\n1. 测试",
            "开始生成",
            "start generation"
        ]
        
        for i, message in enumerate(test_messages):
            context = {
                'user_initiated': i == 1,  # 只有第二个消息是用户发起的
                'file_name': 'test.xml',
                'chat_history': [{'role': 'user', 'content': f'历史消息{j}'} for j in range(i)]
            }
            
            response = ai_service._mock_chat_response(message, context)
            
            print(f"📝 消息 {i+1}: {message[:20]}...")
            print(f"   success字段: {response.get('success', '缺失')}")
            print(f"   完整响应: {json.dumps(response, indent=2, ensure_ascii=False)[:200]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Mock响应测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试超时和Mock响应场景")
    print("=" * 60)
    
    # 1. 测试Dify超时场景
    timeout_result = await test_dify_timeout_scenario()
    
    # 2. 直接测试chat_with_agent的超时场景
    chat_timeout_result = await test_chat_with_agent_timeout()
    
    # 3. 测试Mock响应的success字段
    mock_test_result = await test_mock_response_without_success_field()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ Dify超时场景: {'成功' if timeout_result and timeout_result.get('success') else '失败'}")
    print(f"✅ 直接对话超时场景: {'成功' if chat_timeout_result and chat_timeout_result.get('success') else '失败'}")
    print(f"✅ Mock响应测试: {'成功' if mock_test_result else '失败'}")
    
    # 分析失败原因
    if timeout_result and not timeout_result.get('success'):
        print(f"❌ Dify超时场景错误: {timeout_result.get('error', 'unknown')}")
    
    if chat_timeout_result and not chat_timeout_result.get('success'):
        print(f"❌ 直接对话超时场景错误: {chat_timeout_result.get('error', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(main())