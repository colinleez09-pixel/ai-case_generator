#!/usr/bin/env python3
"""
测试完整的文件上传和自动分析流程
"""

import asyncio
import json
import logging
from services.generation_service import GenerationService
from services.session_service import SessionService
from services.file_service import FileService
from services.ai_service import AIService
from config import Config
from werkzeug.datastructures import FileStorage
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_file_storage(filename: str, content: str) -> FileStorage:
    """创建模拟的FileStorage对象"""
    return FileStorage(
        stream=io.BytesIO(content.encode('utf-8')),
        filename=filename,
        content_type='application/xml'
    )

async def test_complete_upload_flow():
    """测试完整的上传和自动分析流程"""
    print("🚀 测试完整的文件上传和自动分析流程...")
    
    try:
        # 1. 初始化服务
        print("📋 初始化服务...")
        session_service = SessionService(None)  # 使用内存存储
        file_service = FileService('uploads')
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_service = AIService(ai_config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
        print(f"📊 是否Mock模式: {ai_service.mode_selector.is_mock_mode()}")
        
        # 2. 准备测试文件
        print("📁 准备测试文件...")
        test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <name>CBS系统调账测试</name>
    <description>
        【预置条件】
        1. CBS系统运行正常
        2. 修改系统变量SYS_abc的值为12
        3. 设置变量，初始金额为100

        【测试步骤】
        1. 进行调账，调减20元

        【预期结果】
        1. 调账成功
        2. account_balance表amount字段值为80
    </description>
</testcase>"""
        
        files = {
            'case_template': create_mock_file_storage('test_case.xml', test_xml_content)
        }
        
        config = {}
        
        # 3. 启动生成任务（包含自动分析）
        print("🎯 启动生成任务...")
        result = generation_service.start_generation_task(files, config)
        
        print(f"📝 启动结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            session_id = result['session_id']
            print(f"✅ 任务启动成功，会话ID: {session_id}")
            
            # 检查是否有自动分析结果
            if result.get('auto_chat_started'):
                print("🤖 自动分析已启动")
                print(f"📝 AI回复: {result.get('message', '')}")
                
                # 4. 检查会话状态
                session_data = session_service.get_session_data(session_id)
                print(f"📊 会话状态: {session_data.get('status')}")
                print(f"📊 Dify对话ID: {session_data.get('dify_conversation_id')}")
                
                return True
            else:
                print("⚠️ 自动分析未启动")
                return False
        else:
            print(f"❌ 任务启动失败: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manual_chat_after_upload():
    """测试上传后手动发送消息"""
    print("\n🎯 测试上传后手动发送消息...")
    
    try:
        # 1. 初始化服务
        session_service = SessionService(None)
        file_service = FileService('uploads')
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_service = AIService(ai_config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 2. 先上传文件
        test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <name>用户登录测试</name>
    <description>
        【预置条件】
        1. 系统正常运行
        2. 用户账号存在

        【测试步骤】
        1. 输入用户名和密码
        2. 点击登录按钮

        【预期结果】
        1. 登录成功
        2. 跳转到主页
    </description>
</testcase>"""
        
        files = {
            'case_template': create_mock_file_storage('login_test.xml', test_xml_content)
        }
        
        result = generation_service.start_generation_task(files, {})
        
        if result.get('success'):
            session_id = result['session_id']
            print(f"✅ 文件上传成功，会话ID: {session_id}")
            
            # 3. 手动发送消息给AI
            message = "我上传了一个用户登录的测试用例，请帮我分析并完善"
            context = {
                'session_id': session_id,
                'files_info': result.get('files_info', {}),
                'extracted_content': result.get('extracted_content', '')
            }
            
            print("🚀 发送消息给AI...")
            chat_result = await ai_service.chat_with_agent(session_id, message, context)
            
            print(f"📝 AI回复: {json.dumps(chat_result, indent=2, ensure_ascii=False)}")
            
            if chat_result.get('success', True):  # 默认为True，因为Mock模式不返回success字段
                print("✅ 手动对话成功")
                return True
            else:
                print("❌ 手动对话失败")
                return False
        else:
            print("❌ 文件上传失败")
            return False
            
    except Exception as e:
        print(f"❌ 手动对话测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试完整的文件上传和自动分析流程")
    print("=" * 60)
    
    # 1. 测试完整的自动分析流程
    auto_analysis_result = await test_complete_upload_flow()
    
    # 2. 测试手动对话
    manual_chat_result = await test_manual_chat_after_upload()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 自动分析流程: {'成功' if auto_analysis_result else '失败'}")
    print(f"✅ 手动对话流程: {'成功' if manual_chat_result else '失败'}")
    
    if not auto_analysis_result:
        print("\n❌ 自动分析问题:")
        print("1. 检查GenerationService.auto_analyze_and_chat方法")
        print("2. 检查AI服务的Dify连接")
        print("3. 检查文件解析逻辑")
    
    if not manual_chat_result:
        print("\n❌ 手动对话问题:")
        print("1. 检查AIService.chat_with_agent方法")
        print("2. 检查Dify API调用")

if __name__ == "__main__":
    asyncio.run(main())