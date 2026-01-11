#!/usr/bin/env python3
"""
测试真实的Dify对话连接
验证系统参数的提取和多轮对话功能
"""

import asyncio
import json
import logging
from services.ai_service import AIService
from services.session_service import SessionService
from services.chat_service import ChatService
from config import Config

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_dify_conversation():
    """测试真实的Dify对话连接"""
    
    print("=" * 60)
    print("测试真实的Dify对话连接")
    print("=" * 60)
    
    # 初始化服务
    config = Config()
    ai_config = config.AI_SERVICE_CONFIG
    
    print(f"当前配置:")
    print(f"- Mock模式: {ai_config.get('mock_mode', True)}")
    print(f"- Dify URL: {ai_config.get('dify_url', 'N/A')}")
    print(f"- Dify Token: {'已配置' if ai_config.get('dify_token') else '未配置'}")
    
    # 创建服务实例
    session_service = SessionService(redis_client=None)  # 使用内存存储
    ai_service = AIService(ai_config, redis_client=None)
    chat_service = ChatService(ai_service, session_service)
    
    # 创建测试会话
    session_id = session_service.create_session()
    print(f"\n创建测试会话: {session_id}")
    
    # 设置会话状态为可对话
    session_service.update_session_status(session_id, 'chatting')
    print(f"设置会话状态为: chatting")
    
    try:
        print("\n1. 第一次对话（创建新conversation）")
        print("-" * 40)
        
        # 第一次对话
        message1 = "你好，我想生成一些测试用例"
        print(f"发送消息: {message1}")
        
        response1 = chat_service.send_message(session_id, message1)
        print(f"响应成功: {response1.get('success', False)}")
        print(f"回复内容: {response1.get('reply', 'N/A')[:100]}...")
        
        if response1.get('success'):
            # 检查conversation_id是否被保存
            saved_conversation_id = session_service.get_dify_conversation_id(session_id)
            print(f"保存的conversation_id: {saved_conversation_id}")
            
            # 检查系统参数是否被保存
            saved_system_params = session_service.get_dify_system_params(session_id)
            if saved_system_params:
                print(f"保存的系统参数数量: {len(saved_system_params)}")
                print("关键系统参数:")
                for key in ['sys.user_id', 'sys.app_id', 'sys.conversation_id', 'sys.dialogue_count']:
                    if key in saved_system_params:
                        print(f"  - {key}: {saved_system_params[key]}")
            else:
                print("未保存系统参数")
        
        print("\n2. 第二次对话（使用已有conversation）")
        print("-" * 40)
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 第二次对话
        message2 = "请帮我分析一下登录功能的测试场景"
        print(f"发送消息: {message2}")
        
        response2 = chat_service.send_message(session_id, message2)
        print(f"响应成功: {response2.get('success', False)}")
        print(f"回复内容: {response2.get('reply', 'N/A')[:100]}...")
        
        if response2.get('success'):
            # 检查conversation_id是否保持一致
            current_conversation_id = session_service.get_dify_conversation_id(session_id)
            print(f"当前conversation_id: {current_conversation_id}")
            
            if saved_conversation_id and current_conversation_id == saved_conversation_id:
                print("✓ Conversation ID保持一致，多轮对话成功")
            else:
                print("✗ Conversation ID不一致")
        
        print("\n3. 第三次对话（继续多轮对话）")
        print("-" * 40)
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 第三次对话
        message3 = "我还需要考虑哪些边界情况？"
        print(f"发送消息: {message3}")
        
        response3 = chat_service.send_message(session_id, message3)
        print(f"响应成功: {response3.get('success', False)}")
        print(f"回复内容: {response3.get('reply', 'N/A')[:100]}...")
        
        # 获取对话历史
        history_result = chat_service.get_chat_history(session_id)
        if history_result.get('success'):
            chat_history = history_result.get('chat_history', [])
            print(f"\n对话历史总数: {len(chat_history)}")
            print("最近3条消息:")
            for i, msg in enumerate(chat_history[-3:], 1):
                role = msg.get('role', 'unknown')
                content = msg.get('message', '')[:50]
                print(f"  {i}. [{role}] {content}...")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_real_dify_conversation())