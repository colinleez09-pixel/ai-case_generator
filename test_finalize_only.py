#!/usr/bin/env python3
"""
Test only the finalization and download process
"""
import requests
import json

def test_finalize_download():
    """Test finalization and download"""
    
    # Create session and generate test cases
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps><step>打开登录页面</step></steps>
    </testcase>
</testcases>"""
    
    files = {'case_template': ('test_case.xml', test_xml, 'application/xml')}
    data = {'config': json.dumps({'api_version': 'v1.0'})}
    
    # Start generation
    response = requests.post('http://localhost:5000/api/generation/start', files=files, data=data)
    session_id = response.json().get('session_id')
    print(f"Session ID: {session_id}")
    
    # Chat to trigger generation readiness
    chat_data = {'session_id': session_id, 'message': '开始生成'}
    response = requests.post('http://localhost:5000/api/chat/send', json=chat_data, headers={'Content-Type': 'application/json'})
    print(f"Chat response: {response.status_code}")
    
    # Generate test cases
    gen_data = {'session_id': session_id}
    response = requests.post('http://localhost:5000/api/generation/generate', json=gen_data, headers={'Content-Type': 'application/json'}, stream=True)
    
    print(f"Generation response: {response.status_code}")
    
    # Extract test cases from streaming response
    test_cases = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'complete':
                        test_cases = data.get('data', {}).get('test_cases', [])
                        print(f"Extracted {len(test_cases)} test cases")
                        break
                except json.JSONDecodeError:
                    continue
    
    if not test_cases:
        print("❌ No test cases generated")
        return
    
    # Check session status after generation
    status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"Session status after generation: {status_data.get('status')}")
    
    # Test finalization
    print("\n=== Testing Finalization ===")
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
        print("❌ Finalization failed")
        return
    
    result = response.json()
    file_id = result.get('file_id')
    print(f"Generated file ID: {file_id}")
    
    # Check session status after finalization
    status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"Session status after finalization: {status_data.get('status')}")
    
    # Test download
    print("\n=== Testing Download ===")
    download_url = f'http://localhost:5000/api/generation/download?session_id={session_id}&file_id={file_id}'
    print(f"Download URL: {download_url}")
    
    response = requests.get(download_url)
    print(f"Download status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Download successful! Downloaded {len(response.content)} bytes")
        # Show first 200 chars of content
        content = response.content.decode('utf-8')
        print(f"Content preview: {content[:200]}...")
    else:
        print(f"❌ Download failed: {response.text}")

if __name__ == "__main__":
    test_finalize_download()