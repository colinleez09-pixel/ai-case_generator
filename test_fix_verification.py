#!/usr/bin/env python3
"""
验证修复是否有效
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

async def test_fixed_auto_analysis():
    """测试修复后的自动分析功能"""
    print("🔧 测试修复后的自动分析功能...")
    
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
        
        # 使用Mock模式
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True
        ai_service = AIService(ai_config)
        
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 2. 测试自动分析
        print("🤖 测试自动分析...")
        
        files_info = {
            'case_template': {
                'file_id': 'test_case_template_123',
                'file_path': 'test_case_chinese.xml',
                'original_filename': 'test_case_chinese.xml',
                'file_size': 1024
            }
        }
        
        session_id = 'test_fixed_session'
        result = await generation_service.auto_analyze_and_chat(session_id, files_info)
        
        print("✅ 修复后的自动分析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 验证结果
        success = result.get('success', False)
        print(f"📊 成功状态: {success}")
        
        if success:
            print("🎉 修复成功！自动分析功能正常工作")
            return True
        else:
            print(f"❌ 修复失败，错误: {result.get('error', 'unknown')}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mock_responses():
    """测试所有Mock响应都包含success字段"""
    print("\n🧪 测试所有Mock响应都包含success字段...")
    
    try:
        from services.ai_service import AIService
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_config['mock_mode'] = True
        ai_service = AIService(ai_config)
        
        # 测试不同类型的Mock响应
        test_cases = [
            {
                'name': '文件分析Mock',
                'method': '_mock_file_analysis',
                'args': [{'case_template': {'file_id': 'test'}}]
            },
            {
                'name': '普通对话Mock',
                'method': '_mock_chat_response',
                'args': ['普通消息', {}]
            },
            {
                'name': '自动分析对话Mock',
                'method': '_mock_chat_response',
                'args': ['我上传了一个测试用例文件，以下是文件中的测试用例内容：测试', {'user_initiated': True}]
            },
            {
                'name': '开始生成Mock',
                'method': '_mock_chat_response',
                'args': ['开始生成', {}]
            }
        ]
        
        all_success = True
        
        for test_case in test_cases:
            method = getattr(ai_service, test_case['method'])
            result = method(*test_case['args'])
            
            has_success = 'success' in result
            success_value = result.get('success', False)
            
            print(f"📝 {test_case['name']}: success字段={'存在' if has_success else '缺失'}, 值={success_value}")
            
            if not has_success or not success_value:
                all_success = False
                print(f"   ❌ 问题: {json.dumps(result, ensure_ascii=False)[:100]}...")
        
        if all_success:
            print("🎉 所有Mock响应都包含正确的success字段")
        else:
            print("❌ 部分Mock响应缺少success字段")
        
        return all_success
        
    except Exception as e:
        print(f"❌ Mock响应测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("验证修复是否有效")
    print("=" * 60)
    
    # 1. 测试修复后的自动分析功能
    auto_analysis_success = await test_fixed_auto_analysis()
    
    # 2. 测试所有Mock响应
    mock_responses_success = await test_mock_responses()
    
    print("\n" + "=" * 60)
    print("修复验证总结")
    print("=" * 60)
    
    print(f"✅ 自动分析功能: {'修复成功' if auto_analysis_success else '仍有问题'}")
    print(f"✅ Mock响应完整性: {'修复成功' if mock_responses_success else '仍有问题'}")
    
    if auto_analysis_success and mock_responses_success:
        print("\n🎉 所有修复都成功！自动分析功能应该可以正常工作了。")
    else:
        print("\n❌ 仍有问题需要进一步修复。")

if __name__ == "__main__":
    asyncio.run(main())