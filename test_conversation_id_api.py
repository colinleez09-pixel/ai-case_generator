"""测试带conversation_id的Dify API调用"""
import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_dify_conversation_api():
    """测试Dify对话API的conversation_id处理"""
    
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
    print("测试Dify对话API的conversation_id处理")
    print("=" * 60)
    
    # 第一次对话 - 不带conversation_id
    print("\n1. 第一次对话（不带conversation_id）...")
    chat_data_1 = {
        'inputs': {},
        'query': '你好，我想测试登录功能',
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
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            conversation_id = result.get('conversation_id')
            print(f"   ✅ 成功获得conversation_id: {conversation_id}")
            print(f"   回复: {result.get('answer', '无回复')[:100]}...")
            
            if not conversation_id:
                print("   ❌ 未获得conversation_id")
                return False
                
        else:
            print(f"   ❌ 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False
    
    # 第二次对话 - 带conversation_id
    print(f"\n2. 第二次对话（带conversation_id={conversation_id}）...")
    chat_data_2 = {
        'inputs': {},
        'query': '请帮我生成一些边界测试用例',
        'response_mode': 'blocking',
        'user': 'test_user',
        'conversation_id': conversation_id,  # 使用之前的conversation_id
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
            new_conversation_id = result.get('conversation_id')
            print(f"   ✅ 成功！返回的conversation_id: {new_conversation_id}")
            print(f"   回复: {result.get('answer', '无回复')[:100]}...")
            
            if new_conversation_id == conversation_id:
                print("   ✅ conversation_id一致，多轮对话成功！")
                return True
            else:
                print(f"   ⚠️  conversation_id不一致: {conversation_id} != {new_conversation_id}")
                return False
                
        else:
            print(f"   ❌ 失败: {response.text}")
            
            # 检查是否是404错误
            if response.status_code == 404:
                print("   🔍 这是404错误，可能的原因：")
                print("      1. conversation_id已过期")
                print("      2. API调用方式不正确")
                print("      3. Dify服务端问题")
            
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

if __name__ == '__main__':
    success = test_dify_conversation_api()
    if success:
        print("\n🎉 Dify多轮对话API测试成功！")
    else:
        print("\n❌ Dify多轮对话API测试失败！")