#!/usr/bin/env python3
"""
调试文件上传流程
"""

import json
import logging
from services.file_service import FileService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_xml_extraction():
    """测试XML内容提取"""
    print("🔍 测试XML内容提取...")
    
    # 使用现有的测试文件
    test_file_path = "test_case_chinese.xml"
    
    try:
        # 正确初始化FileService
        file_service = FileService(upload_folder="uploads")
        extracted_content = file_service.extract_test_case_description(test_file_path)
        
        print("✅ XML解析成功")
        print(f"📄 提取的内容长度: {len(extracted_content)} 字符")
        print(f"📄 提取的内容预览:")
        print("-" * 50)
        print(extracted_content[:500] + "..." if len(extracted_content) > 500 else extracted_content)
        print("-" * 50)
        
        return extracted_content
        
    except Exception as e:
        print(f"❌ XML解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_mock_response():
    """测试Mock响应"""
    print("\n🤖 测试Mock响应...")
    
    try:
        # 正确初始化AIService - 使用AI_SERVICE_CONFIG
        from config import Config
        config = Config.AI_SERVICE_CONFIG
        
        from services.ai_service import AIService
        ai_service = AIService(config)
        
        # 模拟用户上传文件后的消息
        test_message = """我上传了一个测试用例文件：test_case_chinese.xml

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
        
        # 测试Mock响应
        response = ai_service._mock_chat_response(test_message, context)
        
        print("✅ Mock响应生成成功")
        print(f"📝 响应内容:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        return response
        
    except Exception as e:
        print(f"❌ Mock响应测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_frontend_data_structure():
    """测试前端数据结构"""
    print("\n🎨 测试前端数据结构...")
    
    # 模拟后端返回给前端的数据
    mock_backend_response = {
        'success': True,
        'session_id': 'test_session_123',
        'message': '我已经分析了您上传的测试用例文件。这个用例包含了基本的测试流程。为了生成更完整的测试用例，我想了解：\n\n1. 这个系统主要的用户群体是谁？\n2. 是否有特殊的安全性要求？\n3. 有什么特殊的业务规则需要考虑吗？',
        'initial_analysis': {
            'description': """【预置条件】
1. CBS系统运行正常
2. 修改系统变量SYS_abc的值为12
3. 设置变量，初始金额为100

【测试步骤】
1. 进行调账，调减20元

【预期结果】
1. 调账成功
2. account_balance表amount字段值为80""",
            'file_count': 1,
            'test_cases_found': 1,
            'extracted_content': '...'
        },
        'auto_chat_started': True,
        'files_processed': 1,
        'extracted_content': '...'
    }
    
    print("✅ 后端数据结构:")
    print(json.dumps(mock_backend_response, indent=2, ensure_ascii=False))
    
    # 模拟前端处理逻辑
    uploaded_file_name = "test_case_chinese.xml"
    
    if mock_backend_response.get('auto_chat_started') and mock_backend_response.get('initial_analysis'):
        user_message = f"我上传了一个测试用例文件：{uploaded_file_name}\n\n"
        
        if mock_backend_response['initial_analysis'].get('description'):
            user_message += f"以下是文件中的测试用例内容：\n\n{mock_backend_response['initial_analysis']['description']}\n\n"
        
        user_message += "请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"
        
        print("\n✅ 前端用户消息:")
        print(user_message)
        print("\n✅ 前端AI回复:")
        print(mock_backend_response.get('message', ''))
    else:
        print("❌ 前端处理失败")

if __name__ == "__main__":
    print("=" * 60)
    print("调试文件上传自动分析流程")
    print("=" * 60)
    
    # 1. 测试XML提取
    extracted_content = test_xml_extraction()
    
    # 2. 测试Mock响应
    mock_response = test_mock_response()
    
    # 3. 测试前端数据结构
    test_frontend_data_structure()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)