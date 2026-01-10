#!/usr/bin/env python3
"""
Test chat functionality
"""
import requests
import json

def test_chat_flow():
    """Test the complete chat flow"""
    
    # Step 1: Start generation to get session_id
    print("1. Starting generation...")
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps>
            <step>打开登录页面</step>
            <step>输入用户名密码</step>
            <step>点击登录按钮</step>
        </steps>
    </testcase>
</testcases>"""
    
    files = {
        'case_template': ('test_case.xml', test_xml, 'application/xml')
    }
    
    data = {
        'config': json.dumps({'api_version': 'v1.0'})
    }
    
    response = requests.post('http://localhost:5000/api/generation/start', 
                           files=files, data=data)
    
    if response.status_code != 200:
        print(f"Failed to start generation: {response.text}")
        return False
    
    result = response.json()
    session_id = result.get('session_id')
    print(f"Session ID: {session_id}")
    
    # Step 2: Send chat messages
    print("\n2. Testing chat messages...")
    
    messages = [
        "我需要生成登录功能的测试用例",
        "主要测试正常登录和异常登录场景",
        "需要包含用户名密码验证",
        "开始生成"
    ]
    
    for i, message in enumerate(messages):
        print(f"\nSending message {i+1}: {message}")
        
        chat_data = {
            'session_id': session_id,
            'message': message
        }
        
        response = requests.post('http://localhost:5000/api/chat/send',
                               json=chat_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"AI Reply: {result.get('message', 'No message')}")
            print(f"Ready to generate: {result.get('ready_to_generate', False)}")
            
            if result.get('ready_to_generate'):
                print("✓ Ready to generate test cases!")
                return session_id
        else:
            print(f"Error: {response.text}")
            return False
    
    return session_id

def test_generation_flow(session_id):
    """Test the generation flow"""
    print(f"\n3. Testing generation with session: {session_id}")
    
    gen_data = {
        'session_id': session_id
    }
    
    response = requests.post('http://localhost:5000/api/generation/generate',
                           json=gen_data,
                           headers={'Content-Type': 'application/json'},
                           stream=True)
    
    print(f"Generation Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Streaming response:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                        print(f"  {data.get('type', 'unknown')}: {data}")
                        
                        if data.get('type') == 'complete':
                            print("✓ Generation completed!")
                            return True
                    except json.JSONDecodeError:
                        print(f"  Raw: {line_str}")
    else:
        print(f"Error: {response.text}")
    
    return False

if __name__ == "__main__":
    print("Testing complete chat and generation flow...")
    
    session_id = test_chat_flow()
    if session_id:
        test_generation_flow(session_id)
    else:
        print("Chat flow failed!")