#!/usr/bin/env python3
"""
Simple API test script
"""
import requests
import json

def test_config_api():
    """Test the config API endpoint"""
    try:
        response = requests.get('http://localhost:5000/api/config/all')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generation_start():
    """Test the generation start endpoint with a simple file"""
    try:
        # Create a simple test XML file
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
        print(f"Generation Start Status Code: {response.status_code}")
        print(f"Generation Start Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False), result.get('session_id')
        
        return False, None
        
    except Exception as e:
        print(f"Generation Start Error: {e}")
        return False, None

if __name__ == "__main__":
    print("Testing API endpoints...")
    
    print("\n1. Testing config API...")
    config_ok = test_config_api()
    
    print("\n2. Testing generation start...")
    gen_ok, session_id = test_generation_start()
    
    print(f"\nResults:")
    print(f"Config API: {'✓' if config_ok else '✗'}")
    print(f"Generation Start: {'✓' if gen_ok else '✗'}")
    if session_id:
        print(f"Session ID: {session_id}")