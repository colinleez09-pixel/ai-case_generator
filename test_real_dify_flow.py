#!/usr/bin/env python3
"""
测试真实Dify自动分析流程
"""

import requests
import json
import time
from io import BytesIO

def test_real_dify_auto_analysis():
    """测试真实Dify自动分析流程"""
    print("🚀 测试真实Dify自动分析流程...")
    
    base_url = "http://localhost:5000"
    
    # 1. 检查应用状态
    print("📋 检查应用状态...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 应用运行正常")
        else:
            print("❌ 应用状态异常")
            return False
    except:
        print("❌ 无法连接到应用")
        return False
    
    # 2. 准备测试XML文件
    print("📁 准备测试XML文件...")
    test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <name>CBS系统调账功能测试</name>
    <description>测试CBS系统的调账功能，验证账户余额的正确性</description>
    <preconditions>
        <condition>CBS系统运行正常</condition>
        <condition>修改系统变量SYS_abc的值为12</condition>
        <condition>设置变量，初始金额为100</condition>
    </preconditions>
    <steps>
        <step>登录CBS系统</step>
        <step>进入调账功能模块</step>
        <step>进行调账，调减20元</step>
        <step>确认调账操作</step>
    </steps>
    <expected_results>
        <result>调账成功</result>
        <result>account_balance表amount字段值为80</result>
        <result>系统显示调账成功消息</result>
    </expected_results>
</testcase>"""
    
    # 3. 上传文件并启动自动分析
    print("📤 上传文件并启动自动分析...")
    
    files = {
        'case_template': ('cbs_test_case.xml', BytesIO(test_xml_content.encode('utf-8')), 'application/xml')
    }
    
    data = {
        'config': json.dumps({
            'test_type': 'functional',
            'priority': 'high'
        })
    }
    
    try:
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
            if not session_id:
                print("❌ 未获取到会话ID")
                return False
            
            print(f"📋 会话ID: {session_id}")
            
            # 检查是否启动了自动分析
            if upload_result.get('auto_chat_started'):
                print("🤖 自动分析已启动!")
                print(f"📝 AI回复: {upload_result.get('message', '无回复')}")
                
                # 4. 测试后续对话
                print("\n💬 测试后续对话...")
                
                user_message = "我希望这个测试用例能够覆盖更多的异常场景，比如余额不足、系统异常等情况。请帮我完善这个测试用例。"
                
                chat_data = {
                    'message': user_message,
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
                    print("✅ 对话成功!")
                    print(f"📝 AI回复: {chat_result.get('reply', '无回复')}")
                    
                    # 检查是否是真实Dify响应
                    if 'conversation_id' in chat_result and chat_result.get('reply'):
                        print("🎉 确认收到真实Dify响应!")
                        return True
                    else:
                        print("⚠️ 可能仍在使用Mock响应")
                        return False
                else:
                    print(f"❌ 对话失败: {chat_response.text}")
                    return False
            else:
                print("⚠️ 自动分析未启动，可能需要手动发送消息")
                return False
        else:
            print(f"❌ 文件上传失败: {upload_response.status_code}")
            print(f"📝 错误内容: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def check_ai_service_mode():
    """检查AI服务模式"""
    print("🔍 检查AI服务模式...")
    
    try:
        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        from config import Config
        config = Config.AI_SERVICE_CONFIG
        
        print(f"📊 配置信息:")
        print(f"  DIFY_URL: {config['dify_url']}")
        print(f"  MOCK_MODE: {config['mock_mode']}")
        print(f"  TIMEOUT: {config['timeout']}")
        
        if config['mock_mode']:
            print("⚠️ 警告：当前配置为Mock模式!")
            return False
        else:
            print("✅ 配置为Dify模式")
            return True
            
    except Exception as e:
        print(f"❌ 检查配置异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("真实Dify自动分析流程测试")
    print("=" * 60)
    
    # 1. 检查配置
    config_ok = check_ai_service_mode()
    
    if not config_ok:
        print("❌ 配置检查失败，请确保AI_MOCK_MODE=false")
        exit(1)
    
    # 2. 测试完整流程
    flow_success = test_real_dify_auto_analysis()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    if flow_success:
        print("🎉 真实Dify自动分析流程测试成功!")
        print("✅ 文件上传自动解析正常")
        print("✅ Dify自动分析启动正常")
        print("✅ 多轮对话功能正常")
        print("✅ 收到真实Dify响应")
    else:
        print("❌ 真实Dify流程存在问题")
        print("📝 请检查:")
        print("1. Dify连接是否正常")
        print("2. 自动分析逻辑是否正确")
        print("3. 前后端API调用是否正确")