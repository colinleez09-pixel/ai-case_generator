#!/usr/bin/env python3
"""
测试实际错误场景
"""

import asyncio
import json
import logging
from services.file_service import FileService
from services.session_service import SessionService
from services.generation_service import GenerationService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dify_connection_failure_scenario():
    """测试Dify连接失败的场景"""
    print("🔥 测试Dify连接失败场景...")
    
    try:
        # 1. 初始化服务 - 使用真实的Dify配置（会失败）
        print("📋 初始化服务（使用真实Dify配置）...")
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
        
        # 使用真实的Dify配置（会导致连接失败）
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = False  # 使用真实Dify，会失败
        ai_service = AIService(ai_config)
        
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 2. 模拟文件上传
        print("📁 模拟文件上传...")
        
        # 创建模拟的文件信息
        files_info = {
            'case_template': {
                'file_id': 'test_case_template_123',
                'file_path': 'test_case_chinese.xml',
                'original_filename': 'test_case_chinese.xml',
                'file_size': 1024
            }
        }
        
        # 3. 测试自动分析和对话（应该会失败然后降级到Mock）
        print("🤖 测试自动分析和对话（预期Dify失败后降级）...")
        session_id = 'test_session_dify_failure'
        
        result = await generation_service.auto_analyze_and_chat(session_id, files_info)
        
        print("✅ 自动分析结果（Dify失败后的降级）:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ Dify连接失败场景测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_chat_with_agent_dify_failure():
    """直接测试chat_with_agent在Dify失败时的行为"""
    print("\n🎯 直接测试chat_with_agent的Dify失败场景...")
    
    try:
        # 初始化AIService，使用真实Dify配置（会失败）
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = False  # 使用真实Dify，会失败
        ai_service = AIService(ai_config)
        
        session_id = 'test_dify_failure_chat'
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
        
        result = await ai_service.chat_with_agent(session_id, message, context)
        
        print("✅ chat_with_agent结果（Dify失败后的降级）:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ chat_with_agent Dify失败测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试实际错误场景")
    print("=" * 60)
    
    # 1. 测试Dify连接失败的完整场景
    dify_failure_result = await test_dify_connection_failure_scenario()
    
    # 2. 直接测试chat_with_agent的Dify失败场景
    chat_failure_result = await test_chat_with_agent_dify_failure()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ Dify失败场景: {'成功' if dify_failure_result and dify_failure_result.get('success') else '失败'}")
    print(f"✅ 直接对话失败场景: {'成功' if chat_failure_result and chat_failure_result.get('success') else '失败'}")
    
    # 分析失败原因
    if dify_failure_result and not dify_failure_result.get('success'):
        print(f"❌ Dify失败场景错误: {dify_failure_result.get('error', 'unknown')}")
    
    if chat_failure_result and not chat_failure_result.get('success'):
        print(f"❌ 直接对话失败场景错误: {chat_failure_result.get('error', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(main())