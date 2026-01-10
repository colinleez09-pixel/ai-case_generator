#!/usr/bin/env python3
"""
Test complete application flow
"""
import requests
import json
import time

def test_complete_workflow():
    """Test the complete workflow from file upload to download"""
    
    print("🚀 Testing Complete AI Test Case Generator Workflow")
    print("=" * 60)
    
    # Step 1: Test config API
    print("\n1️⃣ Testing Configuration API...")
    try:
        response = requests.get('http://localhost:5000/api/config/all')
        if response.status_code == 200:
            print("✅ Config API working")
        else:
            print(f"❌ Config API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Config API error: {e}")
        return False
    
    # Step 2: Start generation with file upload
    print("\n2️⃣ Testing File Upload and Session Creation...")
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="用户登录测试">
        <description>测试用户登录功能的各种场景</description>
        <steps>
            <step>打开登录页面</step>
            <step>输入用户名和密码</step>
            <step>点击登录按钮</step>
            <step>验证登录结果</step>
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
    
    files = {
        'case_template': ('test_cases.xml', test_xml, 'application/xml')
    }
    
    data = {
        'config': json.dumps({
            'api_version': 'v2.0',
            'test_environment': 'staging'
        })
    }
    
    try:
        response = requests.post('http://localhost:5000/api/generation/start', 
                               files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ File upload successful, Session ID: {session_id}")
        else:
            print(f"❌ File upload failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False
    
    # Step 3: Chat interaction
    print("\n3️⃣ Testing AI Chat Interaction...")
    
    chat_messages = [
        "我需要为电商系统生成全面的测试用例",
        "重点关注用户登录、商品搜索、购物车和订单流程",
        "需要包含正常场景和异常场景的测试",
        "请确保覆盖边界值测试和安全性测试",
        "开始生成测试用例"
    ]
    
    ready_to_generate = False
    
    for i, message in enumerate(chat_messages, 1):
        print(f"   💬 Message {i}: {message[:50]}...")
        
        try:
            chat_data = {
                'session_id': session_id,
                'message': message
            }
            
            response = requests.post('http://localhost:5000/api/chat/send',
                                   json=chat_data,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                ai_reply = result.get('message', '')
                ready_to_generate = result.get('ready_to_generate', False)
                
                print(f"   🤖 AI Reply: {ai_reply[:100]}...")
                print(f"   📊 Ready to generate: {ready_to_generate}")
                
                if ready_to_generate:
                    print("✅ Chat interaction successful - AI is ready to generate!")
                    break
                    
                time.sleep(0.5)  # Small delay between messages
                
            else:
                print(f"❌ Chat message failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return False
    
    if not ready_to_generate:
        print("❌ AI not ready to generate after all messages")
        return False
    
    # Step 4: Generate test cases
    print("\n4️⃣ Testing Test Case Generation...")
    
    try:
        gen_data = {
            'session_id': session_id
        }
        
        response = requests.post('http://localhost:5000/api/generation/generate',
                               json=gen_data,
                               headers={'Content-Type': 'application/json'},
                               stream=True)
        
        if response.status_code == 200:
            print("   📡 Streaming generation response...")
            
            test_cases = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            msg_type = data.get('type', 'unknown')
                            
                            if msg_type == 'progress':
                                progress_data = data.get('data', {})
                                stage = progress_data.get('stage', 'unknown')
                                progress = progress_data.get('progress', 0)
                                print(f"   ⏳ {stage}: {progress}%")
                                
                            elif msg_type == 'complete':
                                complete_data = data.get('data', {})
                                test_cases = complete_data.get('test_cases', [])
                                total_count = complete_data.get('total_count', 0)
                                print(f"✅ Generation completed! Generated {total_count} test cases")
                                break
                                
                            elif msg_type == 'error':
                                print(f"❌ Generation error: {data.get('message', 'Unknown error')}")
                                return False
                                
                        except json.JSONDecodeError:
                            continue
            
            if not test_cases:
                print("❌ No test cases generated")
                return False
                
        else:
            print(f"❌ Generation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False
    
    # Step 5: Test finalization
    print("\n5️⃣ Testing File Generation and Download...")
    
    try:
        finalize_data = {
            'session_id': session_id,
            'test_cases': test_cases
        }
        
        response = requests.post('http://localhost:5000/api/generation/finalize',
                               json=finalize_data,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            file_id = result.get('file_id')
            print(f"✅ File generation successful, File ID: {file_id}")
            
            # Test download
            download_url = f'http://localhost:5000/api/generation/download?session_id={session_id}&file_id={file_id}'
            download_response = requests.get(download_url)
            
            if download_response.status_code == 200:
                print("✅ File download successful")
                print(f"   📄 Downloaded {len(download_response.content)} bytes")
            else:
                print(f"❌ Download failed: {download_response.status_code}")
                return False
                
        else:
            print(f"❌ Finalization failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Finalization error: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 COMPLETE WORKFLOW TEST SUCCESSFUL!")
    print("✅ All components working correctly:")
    print("   • Configuration API")
    print("   • File Upload & Session Management")
    print("   • AI Chat Interaction")
    print("   • Test Case Generation")
    print("   • File Generation & Download")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if not success:
        print("\n❌ Workflow test failed!")
        exit(1)
    else:
        print("\n🎯 All tests passed! The application is ready for use.")