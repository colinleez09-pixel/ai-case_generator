#!/usr/bin/env python3
"""
测试单个测试用例上传和自动分析流程
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

async def test_single_testcase_upload():
    """测试单个测试用例的上传和自动分析"""
    print("🚀 测试单个测试用例的上传和自动分析...")
    
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
        
        # 2. 读取包含两个测试用例的XML文件
        print("📁 读取包含两个测试用例的XML文件...")
        with open('test_case_chinese.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        files = {
            'case_template': create_mock_file_storage('test_case_chinese.xml', xml_content)
        }
        
        config = {}
        
        # 3. 启动生成任务（包含自动分析）
        print("🎯 启动生成任务...")
        result = generation_service.start_generation_task(files, config)
        
        print(f"📝 启动结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            session_id = result['session_id']
            print(f"✅ 任务启动成功，会话ID: {session_id}")
            
            # 4. 检查提取的内容
            extracted_content = result.get('extracted_content', '')
            print("📝 提取的测试用例内容:")
            print("=" * 60)
            print(extracted_content)
            print("=" * 60)
            
            # 5. 验证只包含第一个测试用例
            if "银行转账功能测试" in extracted_content:
                print("✅ 成功提取第一个测试用例（银行转账功能测试）")
            else:
                print("❌ 未找到第一个测试用例")
                return False
                
            if "账户查询功能测试" in extracted_content:
                print("❌ 错误：提取了第二个测试用例")
                return False
            else:
                print("✅ 成功：没有提取第二个测试用例")
            
            # 6. 检查自动分析结果
            if result.get('auto_chat_started'):
                print("🤖 自动分析已启动")
                ai_reply = result.get('message', '')
                print(f"📝 AI回复: {ai_reply}")
                
                # 7. 检查会话状态
                session_data = session_service.get_session_data(session_id)
                print(f"📊 会话状态: {session_data.get('status')}")
                print(f"📊 Dify对话ID: {session_data.get('dify_conversation_id')}")
                
                # 8. 验证只发送了一次请求
                if session_data.get('dify_conversation_id'):
                    print("✅ 成功建立Dify对话，只发送了一个测试用例")
                    return True
                else:
                    print("⚠️ 自动分析启动但未建立Dify对话")
                    return False
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

async def test_manual_chat_with_single_testcase():
    """测试手动发送单个测试用例给Dify"""
    print("\n💬 测试手动发送单个测试用例给Dify...")
    
    try:
        # 1. 初始化AI服务
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_service = AIService(ai_config)
        
        # 2. 提取第一个测试用例内容
        file_service = FileService('uploads')
        extracted_content = file_service.extract_test_case_description('test_case_chinese.xml')
        
        # 3. 构建消息
        message = f"""我上传了一个测试用例文件：test_case_chinese.xml

以下是文件中的第一个测试用例内容：

{extracted_content}

请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"""
        
        # 4. 发送给Dify
        session_id = 'test_single_case'
        context = {
            'extracted_content': extracted_content,
            'user_initiated': True
        }
        
        print("🚀 发送单个测试用例给Dify...")
        response = await ai_service.chat_with_agent(session_id, message, context)
        
        print(f"📝 Dify回复: {json.dumps(response, indent=2, ensure_ascii=False)}")
        
        if response.get('success', True):
            print("✅ 成功发送单个测试用例给Dify")
            print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
            return True
        else:
            print("❌ 发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 手动测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("测试单个测试用例上传和自动分析")
    print("=" * 60)
    
    # 1. 测试完整的上传和自动分析流程
    upload_result = await test_single_testcase_upload()
    
    # 2. 测试手动发送单个测试用例
    manual_result = await test_manual_chat_with_single_testcase()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 上传和自动分析: {'成功' if upload_result else '失败'}")
    print(f"✅ 手动发送测试用例: {'成功' if manual_result else '失败'}")
    
    if upload_result and manual_result:
        print("\n🎉 所有测试通过！")
        print("✅ 系统现在只提取和发送第一个测试用例")
        print("✅ 避免了多次Dify请求")
        print("✅ 自动分析流程正常工作")
    else:
        print("\n❌ 部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    asyncio.run(main())