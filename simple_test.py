#!/usr/bin/env python3
"""简化的对话测试"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_simple_conversation():
    print("开始简化测试...")
    
    # 1. 创建会话
    print("1. 创建会话...")
    try:
        response = requests.post(f"{BASE_URL}/api/generation/create-session", timeout=10)
        if response.status_code != 200:
            print(f"创建会话失败: {response.text}")
            return
        
        session_data = response.json()
        session_id = session_data.get('session_id')
        print(f"   会话ID: {session_id}")
    except Exception as e:
        print(f"创建会话异常: {e}")
        return
    
    # 2. 第一次对话
    print("2. 第一次对话...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            json={'session_id': session_id, 'message': '你好，我想测试登录功能'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   成功: {result.get('success')}")
            if result.get('success'):
                reply = result.get('message', '')[:100]
                print(f"   回复: {reply}...")
                
                # 判断是否是Dify回复
                if '我已经分析了您上传的文件' in reply:
                    print("   ⚠️  这是Mock回复")
                else:
                    print("   ✅ 这是Dify回复")
            else:
                print(f"   错误: {result.get('message')}")
                return
        else:
            print(f"   HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"第一次对话异常: {e}")
        return
    
    # 等待一下
    print("   等待2秒...")
    time.sleep(2)
    
    # 3. 第二次对话
    print("3. 第二次对话...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            json={'session_id': session_id, 'message': '请帮我生成一些边界测试用例'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   成功: {result.get('success')}")
            if result.get('success'):
                reply = result.get('message', '')[:100]
                print(f"   回复: {reply}...")
                
                # 判断是否是Dify回复
                if '我已经分析了您上传的文件' in reply:
                    print("   ⚠️  这是Mock回复，说明多轮对话失败")
                else:
                    print("   ✅ 这是Dify回复，多轮对话成功！")
            else:
                print(f"   错误: {result.get('message')}")
        else:
            print(f"   HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"第二次对话异常: {e}")
    
    print("测试完成！")

if __name__ == '__main__':
    test_simple_conversation()