#!/usr/bin/env python3
"""
Final comprehensive test of all functionality
"""
import requests
import json
import time

def test_all_functionality():
    """Test all functionality comprehensively"""
    
    print("🔥 FINAL COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test 1: Configuration API
    print("\n1️⃣ Configuration API Test")
    try:
        response = requests.get('http://localhost:5000/api/config/all')
        assert response.status_code == 200
        config_data = response.json()
        assert config_data['success'] == True
        assert 'api_versions' in config_data['config']
        assert 'preset_steps' in config_data['config']
        assert 'preset_components' in config_data['config']
        print("✅ Configuration API working correctly")
    except Exception as e:
        print(f"❌ Configuration API failed: {e}")
        return False
    
    # Test 2: File Upload and Session Creation
    print("\n2️⃣ File Upload and Session Management Test")
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="用户登录测试">
        <description>测试用户登录功能</description>
        <steps>
            <step>打开登录页面</step>
            <step>输入用户名和密码</step>
            <step>点击登录按钮</step>
        </steps>
        <expected>成功登录并跳转到主页</expected>
    </testcase>
    <testcase id="TC002" name="商品搜索测试">
        <description>测试商品搜索功能</description>
        <steps>
            <step>进入商品页面</step>
            <step>输入搜索关键词</step>
            <step>点击搜索按钮</step>
        </steps>
        <expected>显示相关商品列表</expected>
    </testcase>
</testcases>"""
    
    try:
        files = {'case_template': ('comprehensive_test.xml', test_xml, 'application/xml')}
        data = {'config': json.dumps({'api_version': 'v2.1', 'environment': 'test'})}
        
        response = requests.post('http://localhost:5000/api/generation/start', files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] == True
        session_id = result['session_id']
        assert session_id.startswith('sess_')
        print(f"✅ File upload successful, Session: {session_id}")
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return False
    
    # Test 3: Session Persistence
    print("\n3️⃣ Session Persistence Test")
    try:
        status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['success'] == True
        assert status_data['status'] == 'analyzing'
        print("✅ Session persistence working correctly")
    except Exception as e:
        print(f"❌ Session persistence failed: {e}")
        return False
    
    # Test 4: Chat Interaction
    print("\n4️⃣ AI Chat Interaction Test")
    chat_messages = [
        "我需要为电商平台生成全面的测试用例",
        "重点关注用户登录、商品搜索、购物车和支付流程",
        "需要包含正常场景、异常场景和边界值测试",
        "请确保覆盖安全性测试和性能测试",
        "开始生成测试用例"
    ]
    
    try:
        ready_to_generate = False
        for i, message in enumerate(chat_messages, 1):
            chat_data = {'session_id': session_id, 'message': message}
            response = requests.post('http://localhost:5000/api/chat/send', 
                                   json=chat_data, 
                                   headers={'Content-Type': 'application/json'})
            assert response.status_code == 200
            result = response.json()
            assert result['success'] == True
            
            print(f"   💬 Message {i}: {message[:40]}...")
            print(f"   🤖 AI: {result['message'][:60]}...")
            
            if result.get('ready_to_generate'):
                ready_to_generate = True
                print("   🎯 AI is ready to generate!")
                break
            
            time.sleep(0.3)  # Small delay between messages
        
        assert ready_to_generate, "AI should be ready to generate after conversation"
        print("✅ Chat interaction working correctly")
    except Exception as e:
        print(f"❌ Chat interaction failed: {e}")
        return False
    
    # Test 5: Test Case Generation
    print("\n5️⃣ Test Case Generation Test")
    try:
        gen_data = {'session_id': session_id}
        response = requests.post('http://localhost:5000/api/generation/generate',
                               json=gen_data,
                               headers={'Content-Type': 'application/json'},
                               stream=True)
        assert response.status_code == 200
        
        test_cases = []
        progress_updates = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        msg_type = data.get('type')
                        
                        if msg_type == 'progress':
                            progress_updates += 1
                            progress_data = data.get('data', {})
                            print(f"   ⏳ {progress_data.get('stage', 'unknown')}: {progress_data.get('progress', 0)}%")
                            
                        elif msg_type == 'complete':
                            complete_data = data.get('data', {})
                            test_cases = complete_data.get('test_cases', [])
                            total_count = complete_data.get('total_count', 0)
                            print(f"   🎉 Generated {total_count} test cases")
                            break
                            
                        elif msg_type == 'error':
                            raise Exception(f"Generation error: {data.get('message')}")
                            
                    except json.JSONDecodeError:
                        continue
        
        assert len(test_cases) > 0, "Should generate at least one test case"
        assert progress_updates > 0, "Should receive progress updates"
        print("✅ Test case generation working correctly")
    except Exception as e:
        print(f"❌ Test case generation failed: {e}")
        return False
    
    # Test 6: File Generation and Download
    print("\n6️⃣ File Generation and Download Test")
    try:
        finalize_data = {'session_id': session_id, 'test_cases': test_cases}
        response = requests.post('http://localhost:5000/api/generation/finalize',
                               json=finalize_data,
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        result = response.json()
        assert result['success'] == True
        file_id = result['file_id']
        
        print(f"   📄 Generated file: {file_id}")
        
        # Test download
        download_url = f'http://localhost:5000/api/generation/download?session_id={session_id}&file_id={file_id}'
        download_response = requests.get(download_url)
        assert download_response.status_code == 200
        
        content = download_response.content.decode('utf-8')
        assert content.startswith('<?xml version="1.0" ?>')
        assert '<testcases' in content
        assert len(content) > 1000  # Should be substantial content
        
        print(f"   💾 Downloaded {len(content)} characters")
        print("✅ File generation and download working correctly")
    except Exception as e:
        print(f"❌ File generation/download failed: {e}")
        return False
    
    # Test 7: Session Status Verification
    print("\n7️⃣ Final Session Status Test")
    try:
        status_response = requests.get(f'http://localhost:5000/api/generation/status?session_id={session_id}')
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['success'] == True
        assert status_data['status'] == 'finalized'
        print("✅ Final session status correct")
    except Exception as e:
        print(f"❌ Final session status failed: {e}")
        return False
    
    # Success Summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! SYSTEM IS FULLY FUNCTIONAL!")
    print("=" * 60)
    print("✅ Configuration API")
    print("✅ File Upload & Session Management")
    print("✅ Session Persistence")
    print("✅ AI Chat Interaction")
    print("✅ Test Case Generation")
    print("✅ File Generation & Download")
    print("✅ Session Status Management")
    print("=" * 60)
    print("🚀 The AI Test Case Generator is ready for production use!")
    
    return True

if __name__ == "__main__":
    success = test_all_functionality()
    if not success:
        print("\n💥 COMPREHENSIVE TEST FAILED!")
        exit(1)
    else:
        print("\n🎯 COMPREHENSIVE TEST SUCCESSFUL!")
        print("The application is fully functional and ready for use.")