#!/usr/bin/env python3
"""
简单的流式API测试

直接测试Flask应用的流式API端点。
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_streaming_support_directly():
    """直接测试流式支持检查端点"""
    print("🧪 直接测试流式支持检查端点...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 测试GET请求
            response = client.get('/api/chat/streaming/support')
            
            print(f"📡 响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            print(f"📄 响应内容: {response.get_data(as_text=True)}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ 流式支持检查成功: {data}")
                return True
            else:
                print(f"❌ 流式支持检查失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streaming_chat_directly():
    """直接测试流式聊天端点"""
    print("\n🧪 直接测试流式聊天端点...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 首先创建一个会话
            session_response = client.post('/api/generation/create-session', 
                                         json={'user_id': 'test_user'})
            
            if session_response.status_code != 200:
                print(f"❌ 创建会话失败: {session_response.status_code}")
                print(f"📄 响应: {session_response.get_data(as_text=True)}")
                return False
            
            session_data = session_response.get_json()
            session_id = session_data.get('session_id')
            print(f"📋 创建会话成功: {session_id}")
            
            # 测试流式聊天
            chat_data = {
                'session_id': session_id,
                'message': '你好，请帮我分析一下测试用例'
            }
            
            response = client.post('/api/chat/stream', 
                                 json=chat_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"📡 流式聊天响应状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ 流式聊天端点响应成功")
                
                # 读取流式数据
                data = response.get_data(as_text=True)
                print(f"📄 流式数据预览: {data[:200]}...")
                
                return True
            else:
                print(f"❌ 流式聊天失败: {response.status_code}")
                print(f"📄 错误响应: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_route_methods():
    """测试路由支持的HTTP方法"""
    print("\n🧪 测试路由支持的HTTP方法...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            # 测试不同的HTTP方法
            methods_to_test = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
            
            for method in methods_to_test:
                try:
                    if method == 'GET':
                        response = client.get('/api/chat/streaming/support')
                    elif method == 'POST':
                        response = client.post('/api/chat/streaming/support')
                    elif method == 'PUT':
                        response = client.put('/api/chat/streaming/support')
                    elif method == 'DELETE':
                        response = client.delete('/api/chat/streaming/support')
                    elif method == 'OPTIONS':
                        response = client.options('/api/chat/streaming/support')
                    
                    print(f"  {method}: {response.status_code}")
                    
                except Exception as e:
                    print(f"  {method}: 异常 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 方法测试异常: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始简单流式API测试\n")
    print("=" * 60)
    
    # 测试1: 流式支持检查
    support_success = test_streaming_support_directly()
    
    # 测试2: HTTP方法测试
    methods_success = test_route_methods()
    
    # 测试3: 流式聊天端点
    chat_success = test_streaming_chat_directly()
    
    print("\n" + "=" * 60)
    print("📝 测试总结:")
    print(f"✅ 流式支持检查: {'通过' if support_success else '失败'}")
    print(f"✅ HTTP方法测试: {'通过' if methods_success else '失败'}")
    print(f"✅ 流式聊天端点: {'通过' if chat_success else '失败'}")
    
    if all([support_success, methods_success, chat_success]):
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    main()