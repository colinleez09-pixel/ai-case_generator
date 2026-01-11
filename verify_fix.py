#!/usr/bin/env python3
"""验证多轮对话修复"""
import requests
import json

BASE_URL = "http://localhost:5000"

def verify_conversation_fix():
    print("=" * 60)
    print("验证多轮对话修复")
    print("=" * 60)
    
    # 创建会话
    response = requests.post(f"{BASE_URL}/api/generation/create-session")
    session_id = response.json().get('session_id')
    print(f"会话ID: {session_id}")
    
    # 第一次对话
    print("\n第一次对话...")
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={'session_id': session_id, 'message': '你好，我想测试登录功能'}
    )
    result1 = response.json()
    print(f"成功: {result1.get('success')}")
    if result1.get('success'):
        reply1 = result1.get('message', '')
        is_dify1 = '我已经分析了您上传的文件' not in reply1
        print(f"是Dify回复: {is_dify1}")
        print(f"回复片段: {reply1[:50]}...")
    
    # 第二次对话
    print("\n第二次对话...")
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={'session_id': session_id, 'message': '请帮我生成边界测试用例'}
    )
    result2 = response.json()
    print(f"成功: {result2.get('success')}")
    if result2.get('success'):
        reply2 = result2.get('message', '')
        is_dify2 = '我已经分析了您上传的文件' not in reply2
        print(f"是Dify回复: {is_dify2}")
        print(f"回复片段: {reply2[:50]}...")
    
    # 结论
    print("\n" + "=" * 60)
    if result1.get('success') and result2.get('success'):
        if is_dify1 and is_dify2:
            print("✅ 多轮对话修复成功！两次对话都使用了Dify API")
        elif is_dify1 and not is_dify2:
            print("⚠️  第一次成功，第二次降级到Mock模式")
        else:
            print("❌ 对话失败或都使用了Mock模式")
    else:
        print("❌ 对话请求失败")
    print("=" * 60)

if __name__ == '__main__':
    verify_conversation_fix()