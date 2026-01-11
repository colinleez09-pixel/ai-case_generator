#!/usr/bin/env python3
"""
测试Web API功能
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_session_creation():
    """测试会话创建"""
    print("=== 测试会话创建 ===")
    
    response = requests.post(f"{BASE_URL}/api/generation/create-session")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            session_id = data.get('session_id')
            print(f"✅ 会话创建成功: {session_id}")
            return session_id
        else:
            print(f"❌ 会话创建失败: {data.get('message')}")
            return None
    else:
        print(f"❌ 会话创建请求失败: {response.status_code}")
        return None

def test_chat_message(session_id, message):
    """测试聊天消息"""
    print(f"\n=== 测试聊天消息: {message} ===")
    
    payload = {
        'session_id': session_id,
        'message': message
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 聊天成功")
            print(f"AI回复: {data.get('message', '')[:100]}...")
            print(f"准备生成: {data.get('ready_to_generate', False)}")
            return True
        else:
            print(f"❌ 聊天失败: {data.get('message')}")
            return False
    else:
        print(f"❌ 聊天请求失败: {response.status_code}")
        try:
            error_data = response.json()
            print(f"错误详情: {error_data}")
        except:
            print(f"响应内容: {response.text}")
        return False

def test_config_check():
    """测试配置检查"""
    print("\n=== 测试配置检查 ===")
    
    response = requests.get(f"{BASE_URL}/api/config/all")
    
    if response.status_code == 200:
        data = response.json()
        ai_config = data.get('ai_service', {})
        mock_mode = ai_config.get('mock_mode', True)
        
        print(f"Mock模式: {mock_mode}")
        print(f"Dify URL: {ai_config.get('dify_url', 'N/A')}")
        
        if not mock_mode:
            print("✅ 配置正确：Dify模式已启用")
            return True
        else:
            print("❌ 配置错误：仍在Mock模式")
            return False
    else:
        print(f"❌ 配置检查失败: {response.status_code}")
        return False

def main():
    """主测试函数"""
    print("开始测试Web API功能")
    print("=" * 50)
    
    # 1. 检查配置
    config_ok = test_config_check()
    
    # 2. 创建会话
    session_id = test_session_creation()
    if not session_id:
        print("❌ 无法创建会话，测试终止")
        return False
    
    # 3. 测试聊天功能
    chat_ok = test_chat_message(session_id, "你好，我想测试一下对话功能")
    
    if chat_ok:
        # 4. 测试更多消息
        test_chat_message(session_id, "我需要生成用户登录功能的测试用例")
        test_chat_message(session_id, "开始生成")
    
    print("\n" + "=" * 50)
    if config_ok and chat_ok:
        print("🎉 Web API测试成功！Dify模式正常工作")
        return True
    else:
        print("⚠️ Web API测试部分失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)