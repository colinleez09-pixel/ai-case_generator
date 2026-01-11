#!/usr/bin/env python3
"""
测试新的文件上传流程
验证修改后的逻辑：
1. 上传文件并点击开始生成
2. 前端显示用户发送文件名和用例描述
3. 后端以用户身份发送给Dify
4. 等待Dify回复
"""

import asyncio
import json
import logging
from services.generation_service import GenerationService
from services.file_service import FileService
from services.session_service import SessionService
from services.ai_service import AIService
from werkzeug.datastructures import FileStorage
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockFileStorage:
    """模拟文件上传对象"""
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
        self.stream = io.BytesIO(content.encode('utf-8'))
    
    def read(self):
        return self.content.encode('utf-8')
    
    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.content)

async def test_new_upload_flow():
    """测试新的上传流程"""
    
    # 1. 初始化服务
    file_service = FileService()
    session_service = SessionService()
    ai_service = AIService()
    generation_service = GenerationService(file_service, session_service, ai_service)
    
    # 2. 准备测试文件
    test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="用户登录功能测试">
        <preconditions>
            <precondition index="1" name="用户已注册账号">
                <description>确保测试用户账号存在于系统中</description>
            </precondition>
        </preconditions>
        <steps>
            <step index="1" name="打开登录页面">
                <description>访问系统登录页面</description>
            </step>
            <step index="2" name="输入用户名和密码">
                <description>输入有效的用户名和密码</description>
            </step>
            <step index="3" name="点击登录按钮">
                <description>点击登录按钮提交表单</description>
            </step>
        </steps>
        <expectedResults>
            <expectedResult index="1" name="成功跳转到用户仪表板页面">
                <description>验证页面跳转到正确的用户仪表板</description>
            </expectedResult>
        </expectedResults>
    </testcase>
</testcases>"""
    
    mock_file = MockFileStorage("login_test_case.xml", test_xml_content)
    
    files = {
        'case_template': mock_file
    }
    
    config = {
        'api_version': 'v2.0'
    }
    
    print("🚀 开始测试新的上传流程...")
    
    try:
        # 3. 调用启动生成任务
        result = generation_service.start_generation_task(files, config)
        
        print("📋 生成任务启动结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 4. 验证结果
        if result.get('success'):
            print("✅ 任务启动成功")
            
            if result.get('auto_chat_started'):
                print("✅ 自动分析已启动")
                print(f"📝 AI回复: {result.get('message', 'N/A')}")
                
                if result.get('extracted_content'):
                    print("✅ 成功提取用例内容")
                    print(f"📄 提取的内容: {result.get('extracted_content')[:200]}...")
                else:
                    print("⚠️ 未提取到用例内容")
                
                if result.get('initial_analysis', {}).get('description'):
                    print("✅ 分析结果包含描述信息")
                else:
                    print("⚠️ 分析结果缺少描述信息")
            else:
                print("⚠️ 自动分析未启动")
        else:
            print(f"❌ 任务启动失败: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

def test_frontend_message_format():
    """测试前端消息格式"""
    print("\n🎨 测试前端消息格式...")
    
    # 模拟前端接收到的响应数据
    mock_response = {
        'success': True,
        'session_id': 'test_session_123',
        'message': '我已经分析了您上传的测试用例。这是一个用户登录功能的测试用例，包含了基本的登录流程。为了生成更完整的测试用例，我想了解：\n\n1. 这个登录系统是否支持多种登录方式（如邮箱、手机号）？\n2. 是否需要考虑密码强度验证？\n3. 是否有登录失败次数限制？',
        'initial_analysis': {
            'description': """【预置条件】
1. 用户已注册账号 - 确保测试用户账号存在于系统中

【测试步骤】
1. 打开登录页面 - 访问系统登录页面
2. 输入用户名和密码 - 输入有效的用户名和密码
3. 点击登录按钮 - 点击登录按钮提交表单

【预期结果】
1. 成功跳转到用户仪表板页面 - 验证页面跳转到正确的用户仪表板""",
            'file_count': 1,
            'test_cases_found': 1
        },
        'auto_chat_started': True,
        'files_processed': 1,
        'extracted_content': '...'
    }
    
    # 模拟前端处理逻辑
    uploaded_file_name = "login_test_case.xml"
    
    if mock_response.get('auto_chat_started') and mock_response.get('initial_analysis'):
        user_message = f"我上传了一个测试用例文件：{uploaded_file_name}\n\n"
        
        if mock_response['initial_analysis'].get('description'):
            user_message += f"以下是文件中的测试用例内容：\n\n{mock_response['initial_analysis']['description']}\n\n"
        
        user_message += "请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"
        
        print("👤 用户消息:")
        print(user_message)
        print("\n🤖 AI回复:")
        print(mock_response.get('message', ''))
        print("\n✅ 前端消息格式测试完成")
    else:
        print("❌ 前端消息格式测试失败")

if __name__ == "__main__":
    print("=" * 60)
    print("测试新的文件上传自动分析流程")
    print("=" * 60)
    
    # 测试后端逻辑
    asyncio.run(test_new_upload_flow())
    
    # 测试前端消息格式
    test_frontend_message_format()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)