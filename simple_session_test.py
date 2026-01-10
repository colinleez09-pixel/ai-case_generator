#!/usr/bin/env python3
"""
Simple session persistence test
"""
import requests
import json

def test_session_persistence():
    """Test if session data persists across requests"""
    
    # Create session
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps><step>打开登录页面</step></steps>
    </testcase>
</testcases>"""
    
    files = {'case_template': ('test_case.xml', test_xml, 'application/xml')}
    data = {'config': json.dumps({'api_version': 'v1.0'})}
    
    print("Creating session...")
    response = requests.post('http://localhost:5000/api/generation/start', files=files, data=data)
    
    if response.status_code != 200:
        print(f"Failed to create session: {response.text}")
        return
    
    result = response.json()
    session_id = result.get('session_id')
    print(f"Session created: {session_id}")
    
    # Test session status immediately
    print("\nTesting session status...")
    status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
    print(f"Status response: {status_response.status_code}")
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"Session status: {status_data.get('status')}")
        print("✅ Session data persists!")
    else:
        print(f"❌ Session not found: {status_response.text}")

if __name__ == "__main__":
    test_session_persistence()