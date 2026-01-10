#!/usr/bin/env python3
"""
Debug download functionality
"""
import requests
import json

def debug_download():
    """Debug the download functionality"""
    
    # Step 1: Create session and generate test cases
    print("1. Creating session and generating test cases...")
    
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
    
    # Start generation
    response = requests.post('http://localhost:5000/api/generation/start', 
                           files=files, data=data)
    
    if response.status_code != 200:
        print(f"Failed to start: {response.text}")
        return
    
    result = response.json()
    session_id = result.get('session_id')
    print(f"Session ID: {session_id}")
    
    # Send chat message to trigger generation
    chat_data = {
        'session_id': session_id,
        'message': '开始生成'
    }
    
    response = requests.post('http://localhost:5000/api/chat/send',
                           json=chat_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code != 200:
        print(f"Chat failed: {response.text}")
        return
    
    # Generate test cases
    gen_data = {
        'session_id': session_id
    }
    
    response = requests.post('http://localhost:5000/api/generation/generate',
                           json=gen_data,
                           headers={'Content-Type': 'application/json'},
                           stream=True)
    
    if response.status_code != 200:
        print(f"Generation failed: {response.text}")
        return
    
    # Process streaming response
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
    
    # Step 2: Test finalization
    print("\n2. Testing finalization...")
    
    finalize_data = {
        'session_id': session_id,
        'test_cases': test_cases
    }
    
    response = requests.post('http://localhost:5000/api/generation/finalize',
                           json=finalize_data,
                           headers={'Content-Type': 'application/json'})
    
    print(f"Finalize status: {response.status_code}")
    print(f"Finalize response: {response.text}")
    
    if response.status_code != 200:
        return
    
    result = response.json()
    file_id = result.get('file_id')
    print(f"File ID: {file_id}")
    
    # Step 3: Test download
    print("\n3. Testing download...")
    
    download_url = f'http://localhost:5000/api/generation/download?session_id={session_id}&file_id={file_id}'
    print(f"Download URL: {download_url}")
    
    response = requests.get(download_url)
    print(f"Download status: {response.status_code}")
    print(f"Download response: {response.text[:200]}...")
    
    if response.status_code == 200:
        print(f"Downloaded {len(response.content)} bytes")
        print("✅ Download successful!")
    else:
        print("❌ Download failed!")

if __name__ == "__main__":
    debug_download()