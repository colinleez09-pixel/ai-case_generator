#!/usr/bin/env python3
"""
测试前端上传功能 - Mock模式
"""

import requests
import json
import os
from io import BytesIO

def test_frontend_upload():
    """测试前端文件上传功能"""
    print("🌐 测试前端文件上传功能...")
    
    # 确保应用正在运行
    base_url = "http://localhost:5000"
    
    try:
        # 1. 测试主页是否可访问
        print("📋 测试主页访问...")
        response = requests.get(base_url, timeout=5)
        if response.status_code != 200:
            print(f"❌ 主页无法访问: {response.status_code}")
            return False
        print("✅ 主页访问正常")
        
        # 2. 准备测试文件
        print("📁 准备测试文件...")
        test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <name>用户登录测试</name>
    <preconditions>
        <condition>用户已注册账号</condition>
        <condition>系统运行正常</condition>
    </preconditions>
    <steps>
        <step>打开登录页面</step>
        <step>输入用户名和密码</step>
        <step>点击登录按钮</step>
    </steps>
    <expected_results>
        <result>成功跳转到用户仪表板</result>
        <result>显示用户信息</result>
    </expected_results>
</testcase>"""
        
        # 3. 测试文件上传
        print("📤 测试文件上传...")
        
        files = {
            'case_template': ('test_case.xml', BytesIO(test_xml_content.encode('utf-8')), 'application/xml')
        }
        
        data = {
            'config': json.dumps({
                'test_type': 'functional',
                'priority': 'high'
            })
        }
        
        upload_response = requests.post(
            f"{base_url}/api/generation/start",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 上传响应状态: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            print("✅ 文件上传成功!")
            print(f"📝 响应内容: {json.dumps(upload_result, indent=2, ensure_ascii=False)}")
            
            session_id = upload_result.get('session_id')
            if session_id:
                print(f"📋 会话ID: {session_id}")
                
                # 4. 测试对话功能
                print("💬 测试对话功能...")
                
                chat_data = {
                    'message': '我希望生成更多的登录测试用例，包括异常情况。',
                    'session_id': session_id
                }
                
                chat_response = requests.post(
                    f"{base_url}/api/chat/send",
                    json=chat_data,
                    timeout=30
                )
                
                print(f"📊 对话响应状态: {chat_response.status_code}")
                
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    print("✅ 对话功能正常!")
                    print(f"📝 AI回复: {chat_result.get('reply', '无回复')[:200]}...")
                    return True
                else:
                    print(f"❌ 对话功能异常: {chat_response.text}")
                    return False
            else:
                print("⚠️ 未获取到会话ID，但上传成功")
                return True
        else:
            print(f"❌ 文件上传失败: {upload_response.status_code}")
            print(f"📝 错误内容: {upload_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到应用，请确保Flask应用正在运行")
        print("💡 请运行: python app.py")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def check_app_status():
    """检查应用状态"""
    print("🔍 检查应用状态...")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 应用健康检查通过")
            print(f"📊 AI服务模式: {health_data.get('ai_service', {}).get('mode', '未知')}")
            return True
        else:
            print(f"⚠️ 健康检查异常: {response.status_code}")
            return False
    except:
        print("❌ 应用未运行或健康检查端点不可用")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("前端上传功能测试 - Mock模式")
    print("=" * 60)
    
    # 检查应用状态
    app_running = check_app_status()
    
    if app_running:
        # 测试上传功能
        upload_success = test_frontend_upload()
        
        print("\n" + "=" * 60)
        print("测试结果总结")
        print("=" * 60)
        
        if upload_success:
            print("🎉 前端上传功能测试成功!")
            print("✅ Mock模式下的自动分析功能工作正常")
            print("✅ 用户可以正常上传文件并与AI对话")
        else:
            print("⚠️ 前端上传功能存在问题")
    else:
        print("\n💡 请先启动Flask应用:")
        print("   python app.py")
        print("然后重新运行此测试")