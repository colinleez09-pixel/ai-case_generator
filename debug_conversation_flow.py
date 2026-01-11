"""调试对话流程，查看conversation_id的处理"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def debug_conversation_flow():
    print("=" * 60)
    print("调试对话流程")
    print("=" * 60)
    
    # 1. 创建会话
    print("\n1. 创建会话...")
    response = requests.post(f"{BASE_URL}/api/generation/create-session")
    if response.status_code != 200:
        print(f"创建会话失败: {response.text}")
        return
    
    session_data = response.json()
    session_id = session_data.get('session_id')
    print(f"   会话ID: {session_id}")
    
    # 2. 发送第一条消息，观察详细过程
    print("\n2. 发送第一条消息...")
    print("   请观察服务器日志中的详细信息...")
    
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            'session_id': session_id,
            'message': '你好，我想测试登录功能，请简单回复即可'
        }
    )
    
    result1 = response.json()
    print(f"   成功: {result1.get('success')}")
    if result1.get('success'):
        print(f"   回复: {result1.get('message', 'N/A')[:100]}...")
    else:
        print(f"   错误: {result1.get('message', 'N/A')}")
        return
    
    # 等待一段时间，让第一次对话完全处理完毕
    print("\n   等待5秒，让第一次对话完全处理...")
    time.sleep(5)
    
    # 3. 立即发送第二条消息
    print("\n3. 发送第二条消息...")
    print("   请观察服务器日志，看conversation_id是否被正确传递...")
    
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            'session_id': session_id,
            'message': '请继续，这是第二条消息'
        }
    )
    
    result2 = response.json()
    print(f"   成功: {result2.get('success')}")
    if result2.get('success'):
        print(f"   回复: {result2.get('message', 'N/A')[:100]}...")
    else:
        print(f"   错误: {result2.get('message', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("调试完成，请检查服务器日志中的以下信息：")
    print("1. 第一次对话是否成功获得conversation_id")
    print("2. 第二次对话是否正确传递了conversation_id")
    print("3. 第二次对话的Dify API调用是否成功")
    print("4. 如果失败，具体的错误信息是什么")

if __name__ == '__main__':
    debug_conversation_flow()