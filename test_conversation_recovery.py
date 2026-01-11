"""测试对话恢复功能 - 验证conversation_id过期后的自动恢复"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_conversation_recovery():
    print("=" * 60)
    print("测试对话恢复功能")
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
    
    # 2. 发送第一条消息
    print("\n2. 发送第一条消息...")
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            'session_id': session_id,
            'message': '你好，我想测试登录功能'
        }
    )
    
    result1 = response.json()
    print(f"   成功: {result1.get('success')}")
    if result1.get('success'):
        print(f"   回复: {result1.get('message', 'N/A')[:100]}...")
    else:
        print(f"   错误: {result1.get('message', 'N/A')}")
        return
    
    # 等待一段时间，让第一次对话完全处理
    print("\n   等待3秒...")
    time.sleep(3)
    
    # 3. 发送第二条消息（可能触发conversation过期）
    print("\n3. 发送第二条消息...")
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            'session_id': session_id,
            'message': '请帮我生成一些边界测试用例'
        }
    )
    
    result2 = response.json()
    print(f"   成功: {result2.get('success')}")
    if result2.get('success'):
        print(f"   回复: {result2.get('message', 'N/A')[:100]}...")
        
        # 检查回复内容，判断是否是Dify回复还是Mock回复
        reply = result2.get('message', '')
        if '我已经分析了您上传的文件' in reply or '请描述一下您希望生成的测试用例类型' in reply:
            print("   ⚠️  这是Mock回复，说明Dify对话可能失败了")
        else:
            print("   ✅ 这看起来是Dify的真实回复")
    else:
        print(f"   错误: {result2.get('message', 'N/A')}")
    
    # 4. 发送第三条消息
    print("\n4. 发送第三条消息...")
    time.sleep(2)
    response = requests.post(
        f"{BASE_URL}/api/chat/send",
        json={
            'session_id': session_id,
            'message': '还需要考虑哪些异常情况？'
        }
    )
    
    result3 = response.json()
    print(f"   成功: {result3.get('success')}")
    if result3.get('success'):
        print(f"   回复: {result3.get('message', 'N/A')[:100]}...")
        
        # 检查回复内容
        reply = result3.get('message', '')
        if '我已经分析了您上传的文件' in reply or '请描述一下您希望生成的测试用例类型' in reply:
            print("   ⚠️  这是Mock回复")
        else:
            print("   ✅ 这看起来是Dify的真实回复")
    else:
        print(f"   错误: {result3.get('message', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n请检查服务器日志，确认：")
    print("1. 第一次对话是否成功获得conversation_id")
    print("2. 第二次对话如果失败，是否检测到conversation过期")
    print("3. 是否自动清除过期的conversation_id并重新开始对话")
    print("4. 后续对话是否使用新的conversation_id")
    print("\n如果看到'Conversation过期，清除并重试'的日志，说明修复生效了！")

if __name__ == '__main__':
    test_conversation_recovery()