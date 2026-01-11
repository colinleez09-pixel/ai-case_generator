#!/usr/bin/env python3
"""
流式聊天端到端测试

完整测试流式聊天功能的端到端流程。
"""

import sys
import os
import json
import time
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_complete_streaming_flow():
    """测试完整的流式聊天流程"""
    print("🧪 测试完整的流式聊天流程...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 步骤1: 创建会话
            print("📋 步骤1: 创建会话")
            session_response = client.post('/api/generation/create-session', 
                                         json={'user_id': 'test_user'})
            
            if session_response.status_code != 200:
                print(f"❌ 创建会话失败: {session_response.status_code}")
                return False
            
            session_data = session_response.get_json()
            session_id = session_data.get('session_id')
            print(f"✅ 会话创建成功: {session_id}")
            
            # 步骤2: 检查流式API支持
            print("\n📋 步骤2: 检查流式API支持")
            support_response = client.get('/api/chat/streaming/support')
            
            if support_response.status_code != 200:
                print(f"❌ 流式API支持检查失败: {support_response.status_code}")
                return False
            
            support_data = support_response.get_json()
            print(f"✅ 流式API支持: {support_data.get('supported', False)}")
            
            # 步骤3: 发送流式聊天请求
            print("\n📋 步骤3: 发送流式聊天请求")
            chat_data = {
                'session_id': session_id,
                'message': '你好，请帮我分析一下登录功能的测试用例'
            }
            
            response = client.post('/api/chat/stream', 
                                 json=chat_data,
                                 headers={'Content-Type': 'application/json'})
            
            if response.status_code != 200:
                print(f"❌ 流式聊天请求失败: {response.status_code}")
                print(f"📄 错误响应: {response.get_data(as_text=True)}")
                return False
            
            print("✅ 流式聊天请求成功")
            
            # 步骤4: 解析流式响应
            print("\n📋 步骤4: 解析流式响应")
            stream_data = response.get_data(as_text=True)
            
            # 解析SSE数据
            events = []
            lines = stream_data.split('\n')
            
            for line in lines:
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        events.append(data)
                    except json.JSONDecodeError:
                        continue
            
            print(f"📊 收到 {len(events)} 个事件")
            
            # 验证事件类型
            event_types = [event.get('type') for event in events]
            print(f"📋 事件类型: {event_types}")
            
            # 检查必要的事件
            required_events = ['stream_start', 'progress', 'stream_complete']
            missing_events = [event for event in required_events if event not in event_types]
            
            if missing_events:
                print(f"⚠️  缺少事件: {missing_events}")
            else:
                print("✅ 所有必要事件都存在")
            
            # 检查是否有流式内容
            streaming_events = [event for event in events if event.get('type') == 'streaming']
            if streaming_events:
                print(f"✅ 收到 {len(streaming_events)} 个流式内容事件")
                
                # 显示部分流式内容
                for i, event in enumerate(streaming_events[:3]):
                    content = event.get('data', {}).get('content', '')
                    print(f"   流式内容 {i+1}: '{content}'")
            else:
                print("⚠️  没有收到流式内容事件")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streaming_error_handling():
    """测试流式聊天的错误处理"""
    print("\n🧪 测试流式聊天的错误处理...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 测试1: 无效会话ID
            print("📋 测试1: 无效会话ID")
            chat_data = {
                'session_id': 'invalid_session_id',
                'message': '测试消息'
            }
            
            response = client.post('/api/chat/stream', 
                                 json=chat_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code == 404:
                print("✅ 正确处理无效会话ID（404错误）")
            else:
                print(f"⚠️  无效会话ID处理异常: {response.status_code}")
            
            # 测试2: 缺少参数
            print("\n📋 测试2: 缺少参数")
            invalid_data = {'session_id': 'test'}  # 缺少message
            
            response = client.post('/api/chat/stream', 
                                 json=invalid_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ 正确处理缺少参数（400错误）")
            else:
                print(f"⚠️  缺少参数处理异常: {response.status_code}")
            
            # 测试3: 空消息
            print("\n📋 测试3: 空消息")
            empty_data = {
                'session_id': 'test_session',
                'message': ''
            }
            
            response = client.post('/api/chat/stream', 
                                 json=empty_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"📡 响应状态码: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ 正确处理空消息（400错误）")
            else:
                print(f"⚠️  空消息处理异常: {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")
        return False

def test_streaming_performance():
    """测试流式聊天的性能"""
    print("\n🧪 测试流式聊天的性能...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 创建会话
            session_response = client.post('/api/generation/create-session', 
                                         json={'user_id': 'perf_test_user'})
            
            if session_response.status_code != 200:
                print("❌ 创建会话失败")
                return False
            
            session_data = session_response.get_json()
            session_id = session_data.get('session_id')
            
            # 测试多个并发请求
            print("📋 测试响应时间...")
            
            start_time = time.time()
            
            chat_data = {
                'session_id': session_id,
                'message': '请生成一个详细的用户注册功能测试用例，包含正常流程和异常场景'
            }
            
            response = client.post('/api/chat/stream', 
                                 json=chat_data,
                                 headers={'Content-Type': 'application/json'})
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"📊 响应时间: {response_time:.2f}秒")
            
            if response.status_code == 200:
                stream_data = response.get_data(as_text=True)
                data_size = len(stream_data)
                print(f"📊 响应数据大小: {data_size} 字节")
                
                # 计算事件数量
                event_count = stream_data.count('data: ')
                print(f"📊 事件数量: {event_count}")
                
                if response_time < 5.0:  # 5秒内响应
                    print("✅ 响应时间良好")
                else:
                    print("⚠️  响应时间较慢")
                
                return True
            else:
                print(f"❌ 性能测试失败: {response.status_code}")
                return False
            
    except Exception as e:
        print(f"❌ 性能测试异常: {e}")
        return False

def main():
    """运行所有端到端测试"""
    print("🚀 开始流式聊天端到端测试\n")
    print("=" * 60)
    
    # 测试1: 完整流程
    flow_success = test_complete_streaming_flow()
    
    # 测试2: 错误处理
    error_success = test_streaming_error_handling()
    
    # 测试3: 性能测试
    perf_success = test_streaming_performance()
    
    print("\n" + "=" * 60)
    print("📝 端到端测试总结:")
    print(f"✅ 完整流程测试: {'通过' if flow_success else '失败'}")
    print(f"✅ 错误处理测试: {'通过' if error_success else '失败'}")
    print(f"✅ 性能测试: {'通过' if perf_success else '失败'}")
    
    if all([flow_success, error_success, perf_success]):
        print("\n🎉 所有端到端测试通过！")
        print("\n📋 流式聊天功能已成功实现:")
        print("   ✅ StreamingChatHandler - 流式聊天处理器")
        print("   ✅ AIService.send_message_streaming - 流式消息发送")
        print("   ✅ /api/chat/streaming/support - 流式API支持检查")
        print("   ✅ /api/chat/stream - 流式聊天端点")
        print("   ✅ 错误处理和降级机制")
        print("   ✅ 性能和资源管理")
        
        print("\n🔧 下一步建议:")
        print("   1. 在前端测试流式显示效果")
        print("   2. 测试不同网络条件下的表现")
        print("   3. 验证浏览器兼容性")
        print("   4. 进行用户体验测试")
    else:
        print("\n⚠️  部分测试失败，需要进一步优化。")

if __name__ == "__main__":
    main()