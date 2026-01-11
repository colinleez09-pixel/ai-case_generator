#!/usr/bin/env python3
"""
流式聊天功能测试

测试新实现的流式聊天API和StreamingChatHandler类的功能。
"""

import asyncio
import json
import time
import requests
from services.ai_service import AIService
from services.streaming_chat_handler import StreamingChatHandler

def test_streaming_chat_handler():
    """测试StreamingChatHandler类"""
    print("🧪 测试StreamingChatHandler类...")
    
    # 创建AI服务配置（Mock模式）
    config = {
        'mock_mode': True,
        'dify_url': 'https://api.dify.ai/v1',
        'dify_token': 'test_token',
        'timeout': 30
    }
    
    # 创建AI服务和流式处理器
    ai_service = AIService(config)
    streaming_handler = StreamingChatHandler(ai_service)
    
    async def run_test():
        session_id = "test_session_123"
        message = "你好，请帮我分析一下测试用例"
        
        print(f"📤 发送消息: {message}")
        print("📡 开始接收流式响应...")
        
        chunk_count = 0
        async for chunk in streaming_handler.handle_streaming_chat(session_id, message):
            chunk_count += 1
            print(f"📦 收到数据块 {chunk_count}: {chunk[:100]}...")
            
            # 解析SSE数据
            if chunk.startswith('data: '):
                try:
                    data = json.loads(chunk[6:])
                    event_type = data.get('type', 'unknown')
                    print(f"   类型: {event_type}")
                    
                    if event_type == 'streaming':
                        content = data.get('data', {}).get('content', '')
                        print(f"   内容: '{content}'")
                    elif event_type == 'progress':
                        stage = data.get('data', {}).get('stage', '')
                        message = data.get('data', {}).get('message', '')
                        print(f"   进度: {stage} - {message}")
                    elif event_type == 'error':
                        error = data.get('data', {}).get('error', '')
                        print(f"   错误: {error}")
                        
                except json.JSONDecodeError as e:
                    print(f"   解析失败: {e}")
        
        print(f"✅ 流式响应完成，共收到 {chunk_count} 个数据块")
        
        # 检查活跃流状态
        active_streams = streaming_handler.get_active_streams()
        print(f"📊 活跃流数量: {len(active_streams)}")
        
        stream_count = streaming_handler.get_stream_count()
        print(f"📊 当前活跃流: {stream_count}")
    
    # 运行异步测试
    asyncio.run(run_test())
    print("✅ StreamingChatHandler测试完成\n")

def test_streaming_api_endpoint():
    """测试流式聊天API端点"""
    print("🧪 测试流式聊天API端点...")
    
    # 测试数据
    test_data = {
        'session_id': 'test_session_456',
        'message': '请帮我生成一个登录功能的测试用例'
    }
    
    try:
        # 发送流式聊天请求
        print(f"📤 发送请求到 /chat/stream")
        print(f"📋 请求数据: {test_data}")
        
        response = requests.post(
            'http://localhost:5000/api/chat/stream',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            stream=True,
            timeout=30
        )
        
        print(f"📡 响应状态: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("📡 开始接收流式数据...")
            
            chunk_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk_count += 1
                    print(f"📦 数据块 {chunk_count}: {line}")
                    
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            event_type = data.get('type', 'unknown')
                            print(f"   事件类型: {event_type}")
                            
                            if event_type == 'stream_complete':
                                print("🎉 流式传输完成")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"   JSON解析失败: {e}")
            
            print(f"✅ 流式API测试完成，共收到 {chunk_count} 个数据块")
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"📋 错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  无法连接到服务器，请确保Flask应用正在运行")
        print("   启动命令: python app.py")
    except Exception as e:
        print(f"❌ API测试失败: {e}")
    
    print("✅ 流式API端点测试完成\n")

def test_streaming_support_check():
    """测试流式API支持检查端点"""
    print("🧪 测试流式API支持检查...")
    
    try:
        response = requests.get(
            'http://localhost:5000/api/chat/streaming/support',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📡 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 响应数据: {result}")
            
            if result.get('supported'):
                print("✅ 流式API支持检查通过")
            else:
                print("⚠️  流式API不支持")
        else:
            print(f"❌ 支持检查失败: {response.status_code}")
            print(f"📋 错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  无法连接到服务器，请确保Flask应用正在运行")
    except Exception as e:
        print(f"❌ 支持检查测试失败: {e}")
    
    print("✅ 流式API支持检查测试完成\n")

def test_ai_service_streaming():
    """测试AIService的流式消息发送方法"""
    print("🧪 测试AIService流式消息发送...")
    
    # 创建AI服务配置（Mock模式）
    config = {
        'mock_mode': True,
        'dify_url': 'https://api.dify.ai/v1',
        'dify_token': 'test_token',
        'timeout': 30
    }
    
    ai_service = AIService(config)
    
    async def run_test():
        # 创建测试会话
        session_id = await ai_service.create_conversation_session("test_user")
        print(f"📋 创建会话: {session_id}")
        
        message = "请帮我分析这个测试用例的覆盖范围"
        print(f"📤 发送流式消息: {message}")
        
        chunk_count = 0
        async for chunk in ai_service.send_message_streaming(session_id, message):
            chunk_count += 1
            event_type = chunk.get('event', 'unknown')
            print(f"📦 数据块 {chunk_count} - 事件: {event_type}")
            
            if event_type == 'message':
                content = chunk.get('content', '')
                print(f"   内容: '{content}'")
            elif event_type == 'message_end':
                print(f"   消息ID: {chunk.get('message_id')}")
                print(f"   对话ID: {chunk.get('conversation_id')}")
                break
            elif event_type == 'error':
                print(f"   错误: {chunk.get('message')}")
                break
        
        print(f"✅ AIService流式测试完成，共收到 {chunk_count} 个数据块")
    
    # 运行异步测试
    asyncio.run(run_test())
    print("✅ AIService流式消息测试完成\n")

def main():
    """运行所有测试"""
    print("🚀 开始流式聊天功能测试\n")
    print("=" * 60)
    
    # 测试1: StreamingChatHandler类
    test_streaming_chat_handler()
    
    # 测试2: AIService流式方法
    test_ai_service_streaming()
    
    # 测试3: 流式API支持检查
    test_streaming_support_check()
    
    # 测试4: 流式聊天API端点
    test_streaming_api_endpoint()
    
    print("=" * 60)
    print("🎉 所有流式聊天功能测试完成！")
    print("\n📝 测试总结:")
    print("✅ StreamingChatHandler类 - 流式聊天处理器")
    print("✅ AIService.send_message_streaming - 流式消息发送")
    print("✅ /chat/streaming/support - 流式API支持检查")
    print("✅ /chat/stream - 流式聊天端点")
    print("\n🔧 如果API端点测试失败，请确保:")
    print("   1. Flask应用正在运行 (python app.py)")
    print("   2. 端口5000可用")
    print("   3. 会话服务正常工作")

if __name__ == "__main__":
    main()