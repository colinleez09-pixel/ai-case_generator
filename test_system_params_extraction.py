#!/usr/bin/env python3
"""
测试系统参数提取功能
验证从Dify返回数据中正确提取和保存系统参数
"""

import asyncio
import json
import logging
from services.ai_service import AIService
from services.session_service import SessionService
from services.chat_service import ChatService
from config import Config

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_system_params_extraction():
    """测试系统参数提取功能"""
    
    print("=" * 60)
    print("测试系统参数提取功能")
    print("=" * 60)
    
    # 初始化服务
    config = Config()
    ai_config = config.AI_SERVICE_CONFIG
    
    # 创建服务实例
    session_service = SessionService(redis_client=None)  # 使用内存存储
    ai_service = AIService(ai_config, redis_client=None)
    chat_service = ChatService(ai_service, session_service)
    
    # 创建测试会话
    session_id = session_service.create_session()
    print(f"创建测试会话: {session_id}")
    
    # 模拟Dify返回的数据（包含系统参数）
    mock_dify_response = {
        "answer": "我已经收到了您的问题，让我来帮您分析一下。",
        "conversation_id": "137783d6-6c82-45ea-94b0-a9a8643f0aff",
        "message_id": "msg_12345",
        "metadata": {
            "files": [],
            "user_id": "a2feec8c-33b1-4266-9168-0ab46ff494d0",
            "app_id": "58ff8bdf-84cf-41de-9442-28527b98a81e",
            "workflow_id": "b5bacd8f-25eb-4847-af68-2c9b7b5ab612",
            "workflow_run_id": "32f140ed-bb19-45fe-93c5-3f47b2c53356",
            "query": "改天再来问你",
            "conversation_id": "137783d6-6c82-45ea-94b0-a9a8643f0aff",
            "dialogue_count": 13
        }
    }
    
    print("\n1. 测试系统参数解析")
    print("-" * 40)
    
    # 测试解析功能
    parsed_response = ai_service._parse_dify_chat_response(mock_dify_response)
    
    print(f"原始响应: {json.dumps(mock_dify_response, indent=2, ensure_ascii=False)}")
    print(f"\n解析后的响应: {json.dumps(parsed_response, indent=2, ensure_ascii=False)}")
    
    # 验证系统参数是否正确提取
    dify_system_params = parsed_response.get('dify_system_params', {})
    print(f"\n提取的系统参数: {json.dumps(dify_system_params, indent=2, ensure_ascii=False)}")
    
    # 验证关键参数
    expected_params = [
        'sys.user_id',
        'sys.app_id', 
        'sys.workflow_id',
        'sys.workflow_run_id',
        'sys.conversation_id',
        'sys.dialogue_count'
    ]
    
    print("\n2. 验证关键参数提取")
    print("-" * 40)
    
    for param in expected_params:
        if param in dify_system_params:
            print(f"✓ {param}: {dify_system_params[param]}")
        else:
            print(f"✗ {param}: 未找到")
    
    print("\n3. 测试系统参数保存到SessionService")
    print("-" * 40)
    
    # 保存系统参数到SessionService
    if dify_system_params:
        success = session_service.update_dify_system_params(session_id, dify_system_params)
        print(f"保存系统参数结果: {'成功' if success else '失败'}")
        
        # 验证保存的参数
        saved_params = session_service.get_dify_system_params(session_id)
        print(f"保存的系统参数: {json.dumps(saved_params, indent=2, ensure_ascii=False)}")
        
        # 验证参数一致性
        if saved_params == dify_system_params:
            print("✓ 系统参数保存和读取一致")
        else:
            print("✗ 系统参数保存和读取不一致")
    
    print("\n4. 测试请求构建（包含系统参数）")
    print("-" * 40)
    
    # 构建包含系统参数的上下文
    context = {
        'dify_conversation_id': mock_dify_response['conversation_id'],
        'dify_system_params': dify_system_params,
        'session_id': session_id
    }
    
    # 测试请求构建
    handler = ai_service.mode_selector.get_handler()
    if hasattr(handler, '_build_chat_request'):
        request_data = handler._build_chat_request(
            conversation_id=mock_dify_response['conversation_id'],
            message="这是一个测试消息",
            context=context,
            stream=False
        )
        
        print(f"构建的请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        # 验证系统参数是否正确添加到inputs中
        inputs = request_data.get('inputs', {})
        print(f"\n请求中的inputs: {json.dumps(inputs, indent=2, ensure_ascii=False)}")
        
        # 验证关键参数是否在inputs中
        print("\n验证inputs中的系统参数:")
        for param in expected_params:
            if param in inputs:
                print(f"✓ {param}: {inputs[param]}")
            else:
                print(f"✗ {param}: 未在inputs中找到")
    
    print("\n5. 测试完整的对话流程")
    print("-" * 40)
    
    # 模拟完整的对话流程
    try:
        # 第一次对话（创建conversation）
        print("发送第一条消息...")
        response1 = chat_service.send_message(session_id, "你好，我想生成一些测试用例")
        print(f"第一次对话响应: {json.dumps(response1, indent=2, ensure_ascii=False)}")
        
        # 检查conversation_id是否被保存
        saved_conversation_id = session_service.get_dify_conversation_id(session_id)
        print(f"保存的conversation_id: {saved_conversation_id}")
        
        # 检查系统参数是否被保存
        saved_system_params = session_service.get_dify_system_params(session_id)
        print(f"保存的系统参数: {json.dumps(saved_system_params, indent=2, ensure_ascii=False)}")
        
        # 第二次对话（使用已有conversation）
        print("\n发送第二条消息...")
        response2 = chat_service.send_message(session_id, "请帮我分析一下登录功能的测试场景")
        print(f"第二次对话响应: {json.dumps(response2, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"对话流程测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_system_params_extraction())