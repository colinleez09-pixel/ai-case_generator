#!/usr/bin/env python3
"""
测试Mock模式下的自动分析功能
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
from services.generation_service import GenerationService
from services.file_service import FileService
from services.session_service import SessionService
from config import Config

async def test_mock_auto_analysis():
    """测试Mock模式下的自动分析功能"""
    print("🤖 测试Mock模式下的自动分析功能...")
    
    try:
        # 1. 初始化服务
        print("📋 初始化服务...")
        
        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(override=True)  # 强制重新加载
        
        # 获取更新后的配置
        config = Config.AI_SERVICE_CONFIG.copy()
        print(f"📊 配置状态: mock_mode={config['mock_mode']}")
        
        # 初始化服务
        upload_folder = Config().UPLOAD_FOLDER
        file_service = FileService(upload_folder)
        session_service = SessionService(redis_client=None)  # 使用内存存储
        ai_service = AIService(config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
        print(f"📊 是否Mock模式: {ai_service.mode_selector.is_mock_mode()}")
        
        # 2. 模拟文件上传
        print("\n📁 模拟文件上传...")
        
        # 创建模拟的文件信息
        mock_files_info = {
            'case_template': {
                'file_id': 'test_file_001',
                'original_filename': 'test_case.xml',
                'file_path': 'test_case_simple.xml',  # 使用现有的测试文件
                'file_size': 1024,
                'upload_time': datetime.utcnow().isoformat()
            }
        }
        
        # 3. 测试自动分析
        print("\n🔍 测试自动分析...")
        
        session_id = 'test_mock_session_001'
        result = await generation_service.auto_analyze_and_chat(session_id, mock_files_info)
        
        print(f"📝 自动分析结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  回复: {result.get('reply', '无回复')[:200]}...")
        print(f"  对话ID: {result.get('conversation_id', '无')}")
        
        # 4. 测试后续对话
        if result.get('success'):
            print("\n💬 测试后续对话...")
            
            # 模拟用户回复
            user_message = "我希望生成登录功能的测试用例，包括正常登录和异常情况。"
            context = {
                'files_info': mock_files_info,
                'conversation_id': result.get('conversation_id')
            }
            
            chat_result = await ai_service.chat_with_agent(session_id, user_message, context)
            
            print(f"📝 对话结果:")
            print(f"  成功: {chat_result.get('success', False)}")
            print(f"  回复: {chat_result.get('reply', '无回复')[:200]}...")
            print(f"  准备生成: {chat_result.get('ready_to_generate', False)}")
        
        # 5. 测试文件分析
        print("\n📊 测试文件分析...")
        
        analysis_result = ai_service.analyze_files(mock_files_info)
        
        print(f"📝 文件分析结果:")
        print(f"  成功: {analysis_result.get('success', False)}")
        print(f"  模板信息: {analysis_result.get('template_info', '无')}")
        print(f"  建议: {len(analysis_result.get('suggestions', []))} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_flow():
    """测试完整的Mock模式流程"""
    print("\n🔄 测试完整的Mock模式流程...")
    
    try:
        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # 初始化服务
        config = Config.AI_SERVICE_CONFIG.copy()
        upload_folder = Config().UPLOAD_FOLDER
        file_service = FileService(upload_folder)
        session_service = SessionService(redis_client=None)  # 使用内存存储
        ai_service = AIService(config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 模拟完整的上传和分析流程
        mock_files = {
            'case_template': type('MockFile', (), {
                'filename': 'test_case.xml',
                'read': lambda: b'<test>mock content</test>',
                'seek': lambda x: None
            })()
        }
        
        mock_config = {
            'test_type': 'functional',
            'priority': 'high'
        }
        
        # 调用启动生成任务
        result = await generation_service._start_generation_task_async(mock_files, mock_config)
        
        print(f"📝 完整流程结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  会话ID: {result.get('session_id', '无')}")
        print(f"  自动对话启动: {result.get('auto_chat_started', False)}")
        print(f"  消息: {result.get('message', '无')[:200]}...")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 完整流程测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("Mock模式自动分析功能测试")
    print("=" * 60)
    
    # 测试1: 基本自动分析功能
    test1_success = await test_mock_auto_analysis()
    
    # 测试2: 完整流程测试
    test2_success = await test_complete_flow()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    print(f"✅ 基本自动分析: {'成功' if test1_success else '失败'}")
    print(f"✅ 完整流程测试: {'成功' if test2_success else '失败'}")
    
    if test1_success and test2_success:
        print("\n🎉 Mock模式下的自动分析功能工作正常！")
        print("📝 现在可以测试前端上传功能了")
    else:
        print("\n⚠️ 部分功能存在问题，需要进一步调试")
    
    return test1_success and test2_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)