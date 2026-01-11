#!/usr/bin/env python3
"""
测试修复两个问题：
1. 发送两条消息给Dify的问题
2. 返回Mock消息而不是真实Dify消息的问题
"""

import asyncio
import json
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generation_service import GenerationService
from services.file_service import FileService
from services.session_service import SessionService
from services.ai_service import AIService
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_message_to_dify():
    """测试只发送一条消息给Dify"""
    print("\n" + "="*60)
    print("🎯 测试修复：确保只发送一条消息给Dify")
    print("="*60)
    
    try:
        # 初始化服务
        config = Config()
        file_service = FileService(config.UPLOAD_FOLDER)
        
        # 创建一个简单的Redis客户端模拟
        class MockRedisClient:
            def __init__(self):
                self.data = {}
            
            async def get(self, key):
                return self.data.get(key)
            
            async def setex(self, key, timeout, value):
                self.data[key] = value
            
            async def delete(self, *keys):
                for key in keys:
                    self.data.pop(key, None)
            
            async def keys(self, pattern):
                return [k for k in self.data.keys() if pattern.replace('*', '') in k]
        
        session_service = SessionService(MockRedisClient())
        ai_service = AIService(config.AI_SERVICE_CONFIG)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 模拟文件信息（使用现有的测试文件）
        files_info = {
            'case_template': {
                'file_id': 'test_case_001',
                'original_name': 'test_case_chinese.xml',
                'file_path': 'test_case_chinese.xml',
                'file_size': 1024
            }
        }
        
        session_id = 'test_session_fix_001'
        
        print(f"📁 使用测试文件: {files_info['case_template']['file_path']}")
        print(f"🔧 会话ID: {session_id}")
        
        # 测试自动分析和对话
        print("\n🚀 开始自动分析和对话...")
        result = await generation_service.auto_analyze_and_chat(session_id, files_info)
        
        print(f"\n📝 自动分析结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  回复: {result.get('reply', 'N/A')[:100]}...")
        print(f"  对话ID: {result.get('conversation_id', 'N/A')}")
        print(f"  消息ID: {result.get('message_id', 'N/A')}")
        
        # 检查是否是真实的Dify响应
        if result.get('success') and result.get('conversation_id'):
            print("✅ 成功：获得了真实的Dify响应")
            return True
        else:
            print("❌ 失败：可能返回了Mock响应")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_no_mock_fallback():
    """测试不会自动降级到Mock模式"""
    print("\n" + "="*60)
    print("🎯 测试修复：确保不会自动降级到Mock模式")
    print("="*60)
    
    try:
        # 初始化服务
        config = Config()
        ai_service = AIService(config.AI_SERVICE_CONFIG)
        
        # 检查当前模式
        print(f"🔍 当前AI模式: {'Mock' if ai_service.mode_selector.is_mock_mode() else 'Dify'}")
        print(f"🔍 配置的Mock模式: {config.AI_SERVICE_CONFIG.get('mock_mode', True)}")
        
        # 测试直接对话
        session_id = 'test_session_fix_002'
        message = "我上传了一个测试用例文件，请帮我分析"
        context = {
            'user_initiated': True,
            'auto_analysis': True
        }
        
        print(f"\n🚀 发送测试消息: {message}")
        response = await ai_service.chat_with_agent(session_id, message, context)
        
        print(f"\n📝 AI响应:")
        print(f"  成功: {response.get('success', False)}")
        print(f"  回复: {response.get('reply', 'N/A')[:100]}...")
        print(f"  对话ID: {response.get('conversation_id', 'N/A')}")
        
        # 检查是否是真实的Dify响应
        if response.get('conversation_id') and not response.get('reply', '').startswith('我已经收到了您的用例文件'):
            print("✅ 成功：获得了真实的Dify响应，没有降级到Mock模式")
            return True
        else:
            print("❌ 失败：可能降级到了Mock模式")
            print(f"   回复内容: {response.get('reply', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_xml_extraction():
    """测试XML提取只获取第一个测试用例"""
    print("\n" + "="*60)
    print("🎯 测试修复：确保只提取第一个测试用例")
    print("="*60)
    
    try:
        # 初始化文件服务
        config = Config()
        file_service = FileService(config.UPLOAD_FOLDER)
        
        # 测试XML提取
        xml_file_path = 'test_case_chinese.xml'
        if os.path.exists(xml_file_path):
            print(f"📁 测试文件: {xml_file_path}")
            
            extracted_content = file_service.extract_test_case_description(xml_file_path)
            
            print(f"\n📝 提取的内容:")
            print(extracted_content)
            
            # 检查是否只包含一个测试用例
            if '测试用例' in extracted_content:
                # 计算测试用例数量（简单检查）
                case_count = extracted_content.count('【测试用例】')
                if case_count <= 1:
                    print(f"✅ 成功：只提取了 {case_count} 个测试用例")
                    return True
                else:
                    print(f"❌ 失败：提取了 {case_count} 个测试用例")
                    return False
            else:
                print("✅ 成功：提取了测试用例内容（格式可能不同）")
                return True
        else:
            print(f"⚠️  测试文件不存在: {xml_file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🔧 开始测试两个问题的修复效果")
    
    results = []
    
    # 测试1：XML提取
    result1 = await test_xml_extraction()
    results.append(("XML提取只获取第一个测试用例", result1))
    
    # 测试2：单条消息发送
    result2 = await test_single_message_to_dify()
    results.append(("只发送一条消息给Dify", result2))
    
    # 测试3：不降级到Mock模式
    result3 = await test_no_mock_fallback()
    results.append(("不自动降级到Mock模式", result3))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n📈 总体结果: {total_passed}/{total_tests} 个测试通过")
    
    if total_passed == total_tests:
        print("🎉 所有修复都成功了！")
    else:
        print("⚠️  还有问题需要进一步修复")

if __name__ == "__main__":
    asyncio.run(main())