#!/usr/bin/env python3
"""
Debug session data persistence
"""
import requests
import json

def debug_session_data():
    """Debug session data persistence across requests"""
    
    # Create session
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps><step>打开登录页面</step></steps>
    </testcase>
</testcases>"""
    
    files = {'case_template': ('test_case.xml', test_xml, 'application/xml')}
    data = {'config': json.dumps({'api_version': 'v1.0'})}
    
    response = requests.post('http://localhost:5000/api/generation/start', files=files, data=data)
    session_id = response.json().get('session_id')
    print(f"Session ID: {session_id}")
    
    # Chat to trigger generation
    chat_data = {'session_id': session_id, 'message': '开始生成'}
    requests.post('http://localhost:5000/api/chat/send', json=chat_data, headers={'Content-Type': 'application/json'})
    
    # Generate test cases
    gen_data = {'session_id': session_id}
    response = requests.post('http://localhost:5000/api/generation/generate', json=gen_data, headers={'Content-Type': 'application/json'}, stream=True)
    
    test_cases = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'complete':
                        test_cases = data.get('data', {}).get('test_cases', [])
                        break
                except json.JSONDecodeError:
                    continue
    
    print(f"Generated {len(test_cases)} test cases")
    
    # Check session status before finalization
    print("\n=== Session Status Before Finalization ===")
    status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
    print(f"Status response: {status_response.status_code}")
    if status_response.status_code == 200:
        print(f"Status data: {json.dumps(status_response.json(), indent=2)}")
    
    # Finalize
    finalize_data = {'session_id': session_id, 'test_cases': test_cases}
    response = requests.post('http://localhost:5000/api/generation/finalize', json=finalize_data, headers={'Content-Type': 'application/json'})
    
    print(f"\n=== Finalization Response ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        file_id = result.get('file_id')
        print(f"File ID: {file_id}")
        
        # Check session status after finalization
        print("\n=== Session Status After Finalization ===")
        status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
        print(f"Status response: {status_response.status_code}")
        if status_response.status_code == 200:
            print(f"Status data: {json.dumps(status_response.json(), indent=2)}")
        
        # Try download
        print(f"\n=== Download Test ===")
        download_url = f'http://localhost:5000/api/generation/download?session_id={session_id}&file_id={file_id}'
        response = requests.get(download_url)
        print(f"Download status: {response.status_code}")
        print(f"Download response: {response.text[:200]}...")

if __name__ == "__main__":
    debug_session_data()