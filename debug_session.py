#!/usr/bin/env python3
"""
Debug session issues
"""
import requests
import json

def debug_session_creation():
    """Debug session creation and retrieval"""
    
    print("1. Testing session creation...")
    
    # Create a session via generation start
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps>
            <step>打开登录页面</step>
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
    
    print(f"Generation start status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        return None
    
    result = response.json()
    session_id = result.get('session_id')
    print(f"Created session: {session_id}")
    
    # Try to send a chat message immediately
    print(f"\n2. Testing immediate chat with session: {session_id}")
    
    chat_data = {
        'session_id': session_id,
        'message': '测试消息'
    }
    
    response = requests.post('http://localhost:5000/api/chat/send',
                           json=chat_data,
                           headers={'Content-Type': 'application/json'})
    
    print(f"Chat status: {response.status_code}")
    print(f"Chat response: {response.text}")
    
    return session_id

if __name__ == "__main__":
    debug_session_creation()