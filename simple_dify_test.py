#!/usr/bin/env python3
"""
简单的Dify连接测试
"""

import requests
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_dify_basic_connection():
    """测试Dify基础连接"""
    print("=== 测试Dify基础连接 ===")
    
    dify_url = os.getenv('DIFY_URL', 'https://api.dify.ai/v1')
    dify_token = os.getenv('DIFY_TOKEN', '')
    
    print(f"Dify URL: {dify_url}")
    print(f"Token: {dify_token[:20]}..." if dify_token else "Token: 未配置")
    
    if not dify_token:
        print("❌ 错误: DIFY_TOKEN 未配置")
        return False
    
    # 测试参数端点
    try:
        headers = {
            'Authorization': f'Bearer {dify_token}',
            'Content-Type': 'application/json'
        }
        
        print("\n1. 测试参数端点...")
        response = requests.get(f'{dify_url}/parameters', headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 参数端点连接成功")
            return True
        else:
            print(f"❌ 参数端点连接失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False


def test_dify_chat_simple():
    """测试简单的Dify对话"""
    print("\n=== 测试简单Dify对话 ===")
    
    dify_url = os.getenv('DIFY_URL', 'https://api.dify.ai/v1')
    dify_token = os.getenv('DIFY_TOKEN', '')
    
    headers = {
        'Authorization': f'Bearer {dify_token}',
        'Content-Type': 'application/json'
    }
    
    # 构建简单的聊天请求
    chat_data = {
        'inputs': {},
        'query': '你好，这是一个测试消息',
        'response_mode': 'blocking',  # 使用阻塞模式，更简单
        'user': 'test_user'
    }
    
    try:
        print("发送聊天请求...")
        response = requests.post(
            f'{dify_url}/chat-messages',
            headers=headers,
            json=chat_data,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 聊天请求成功")
            print(f"回复: {result.get('answer', '无回复')}")
            return True
        else:
            print(f"❌ 聊天请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 聊天请求超时")
        return False
    except Exception as e:
        print(f"❌ 聊天请求错误: {str(e)}")
        return False


def main():
    """主函数"""
    print("开始简单Dify连接测试")
    print("=" * 40)
    
    # 测试基础连接
    connection_ok = test_dify_basic_connection()
    
    if connection_ok:
        # 测试聊天功能
        chat_ok = test_dify_chat_simple()
        
        if chat_ok:
            print("\n🎉 Dify连接和聊天功能都正常！")
            print("现在可以在Web界面中关闭Mock模式进行测试")
        else:
            print("\n⚠️  基础连接正常，但聊天功能有问题")
            print("请检查Dify应用配置和权限")
    else:
        print("\n❌ 基础连接失败")
        print("请检查:")
        print("1. DIFY_TOKEN 是否正确")
        print("2. 网络连接是否正常")
        print("3. Dify服务是否可用")
    
    return connection_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)