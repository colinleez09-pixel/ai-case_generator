#!/usr/bin/env python3
"""
测试完整的自动分析流程
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

async def test_complete_auto_analysis_flow():
    """测试完整的自动分析流程"""
    print("🚀 测试完整的自动分析流程...")
    
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
            
            def delete(self, key):
                if key in self.data:
                    del self.data[key]
                return True
            
            def exists(self, key):
                return key in self.data
        
        mock_redis = MockRedisClient()
        session_service = SessionService(mock_redis)
        
        # 正确初始化AIService，强制使用Mock模式
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True  # 强制使用Mock模式
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
        
        # 3. 测试自动分析和对话
        print("🤖 测试自动分析和对话...")
        session_id = 'test_session_auto_analysis'
        
        result = await generation_service.auto_analyze_and_chat(session_id, files_info)
        
        print("✅ 自动分析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ 自动分析流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_chat_with_agent_directly():
    """直接测试chat_with_agent方法"""
    print("\n🎯 直接测试chat_with_agent方法...")
    
    try:
        # 初始化AIService，强制使用Mock模式
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True  # 强制使用Mock模式
        ai_service = AIService(ai_config)
        
        session_id = 'test_direct_chat'
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
        
        print("✅ chat_with_agent结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ chat_with_agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_generation_service_sync():
    """测试GenerationService的同步包装"""
    print("\n⚙️ 测试GenerationService的同步包装...")
    
    try:
        # 初始化服务
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
            
            def delete(self, key):
                if key in self.data:
                    del self.data[key]
                return True
            
            def exists(self, key):
                return key in self.data
        
        mock_redis = MockRedisClient()
        session_service = SessionService(mock_redis)
        
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True  # 强制使用Mock模式
        ai_service = AIService(ai_config)
        
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 模拟文件上传数据
        from werkzeug.datastructures import FileStorage
        import io
        
        # 读取测试文件内容
        with open('test_case_chinese.xml', 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 创建模拟的FileStorage对象
        file_stream = io.BytesIO(file_content.encode('utf-8'))
        mock_file = FileStorage(
            stream=file_stream,
            filename='test_case_chinese.xml',
            content_type='application/xml'
        )
        
        files = {
            'case_template': mock_file
        }
        
        config = {
            'api_version': 'v2.0'
        }
        
        # 调用同步方法
        result = generation_service.start_generation_task(files, config)
        
        print("✅ start_generation_task结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ GenerationService同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试完整的自动分析流程")
    print("=" * 60)
    
    # 1. 测试完整的自动分析流程
    auto_analysis_result = await test_complete_auto_analysis_flow()
    
    # 2. 直接测试chat_with_agent
    chat_result = await test_chat_with_agent_directly()
    
    # 3. 测试GenerationService的同步包装
    sync_result = test_generation_service_sync()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 自动分析流程: {'成功' if auto_analysis_result and auto_analysis_result.get('success') else '失败'}")
    print(f"✅ 直接对话测试: {'成功' if chat_result and chat_result.get('success') else '失败'}")
    print(f"✅ 同步包装测试: {'成功' if sync_result and sync_result.get('success') else '失败'}")

if __name__ == "__main__":
    asyncio.run(main())