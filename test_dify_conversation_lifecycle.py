"""测试Dify对话生命周期"""
import requests
import json
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_conversation_lifecycle():
    """测试对话的生命周期"""
    
    dify_url = os.getenv('DIFY_URL', 'https://api.dify.ai/v1')
    dify_token = os.getenv('DIFY_TOKEN', '')
    
    if not dify_token:
        print("❌ DIFY_TOKEN未设置")
        return False
    
    headers = {
        'Authorization': f'Bearer {dify_token}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 60)
    print("测试Dify对话生命周期")
    print("=" * 60)
    
    # 第一次对话
    print("\n1. 第一次对话...")
    chat_data_1 = {
        'inputs': {},
        'query': '你好，这是测试消息1',
        'response_mode': 'blocking',
        'user': 'test_user',
        'auto_generate_name': True
    }
    
    try:
        response = requests.post(
            f'{dify_url}/chat-messages',
            headers=headers,
            json=chat_data_1,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            conversation_id = result.get('conversation_id')
            print(f"   ✅ 成功获得conversation_id: {conversation_id}")
            print(f"   回复: {result.get('answer', '无回复')[:50]}...")
        else:
            print(f"   ❌ 失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False
    
    # 立即进行第二次对话（0秒间隔）
    print(f"\n2. 立即进行第二次对话（0秒间隔）...")
    chat_data_2 = {
        'inputs': {},
        'query': '这是测试消息2，立即发送',
        'response_mode': 'blocking',
        'user': 'test_user',
        'conversation_id': conversation_id,
        'auto_generate_name': True
    }
    
    try:
        response = requests.post(
            f'{dify_url}/chat-messages',
            headers=headers,
            json=chat_data_2,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 立即对话成功！")
            print(f"   回复: {result.get('answer', '无回复')[:50]}...")
        else:
            print(f"   ❌ 立即对话失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 立即对话异常: {e}")
    
    # 等待10秒后再试
    print(f"\n3. 等待10秒后再试...")
    time.sleep(10)
    
    chat_data_3 = {
        'inputs': {},
        'query': '这是测试消息3，等待10秒后发送',
        'response_mode': 'blocking',
        'user': 'test_user',
        'conversation_id': conversation_id,
        'auto_generate_name': True
    }
    
    try:
        response = requests.post(
            f'{dify_url}/chat-messages',
            headers=headers,
            json=chat_data_3,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 10秒后对话成功！")
            print(f"   回复: {result.get('answer', '无回复')[:50]}...")
        else:
            print(f"   ❌ 10秒后对话失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 10秒后对话异常: {e}")
    
    # 等待30秒后再试
    print(f"\n4. 等待30秒后再试...")
    time.sleep(30)
    
    chat_data_4 = {
        'inputs': {},
        'query': '这是测试消息4，等待30秒后发送',
        'response_mode': 'blocking',
        'user': 'test_user',
        'conversation_id': conversation_id,
        'auto_generate_name': True
    }
    
    try:
        response = requests.post(
            f'{dify_url}/chat-messages',
            headers=headers,
            json=chat_data_4,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 30秒后对话成功！")
            print(f"   回复: {result.get('answer', '无回复')[:50]}...")
        else:
            print(f"   ❌ 30秒后对话失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 30秒后对话异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("请检查Dify后台的对话记录，确认：")
    print("1. 是否所有成功的消息都在同一个对话中")
    print("2. 对话的超时设置是多少")
    print("3. 是否有相关的配置可以调整")

if __name__ == '__main__':
    test_conversation_lifecycle()