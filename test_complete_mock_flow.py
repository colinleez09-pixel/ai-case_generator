#!/usr/bin/env python3
"""
完整的Mock流程测试脚本
测试从文件上传到测试用例生成的完整流程
"""

import requests
import json
import time
import os
from io import BytesIO

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录功能测试">
        <preconditions>
            <precondition>用户已注册账号</precondition>
        </preconditions>
        <steps>
            <step>打开登录页面</step>
            <step>输入用户名和密码</step>
            <step>点击登录按钮</step>
        </steps>
        <expected_results>
            <result>成功跳转到用户仪表板</result>
        </expected_results>
    </testcase>
</testcases>"""

def create_test_file():
    """创建测试用的XML文件"""
    return BytesIO(TEST_XML_CONTENT.encode('utf-8'))

def test_complete_flow():
    """测试完整的生成流程"""
    print("🚀 开始测试完整的AI测试用例生成流程")
    print("=" * 60)
    
    # 步骤1: 上传文件并启动任务
    print("\n📁 步骤1: 上传文件并启动任务")
    
    files = {
        'case_template': ('test_template.xml', create_test_file(), 'application/xml')
    }
    
    config_data = {
        'api_version': 'v2.0'
    }
    
    data = {
        'config': json.dumps(config_data)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generation/start", files=files, data=data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                session_id = result['session_id']
                print(f"   ✅ 任务启动成功")
                print(f"   📋 会话ID: {session_id}")
                print(f"   💬 初始消息: {result.get('message', 'N/A')}")
            else:
                print(f"   ❌ 任务启动失败: {result.get('message')}")
                return False
        else:
            print(f"   ❌ 请求失败: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到服务器，请确保Flask应用正在运行")
        return False
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False
    
    # 步骤2: 进行对话交互
    print(f"\n💬 步骤2: 进行对话交互")
    
    # 发送几条对话消息
    messages = [
        "我需要生成登录功能的测试用例",
        "请重点测试正常登录和密码错误的场景",
        "开始生成"  # 触发生成的关键词
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"   发送消息 {i}: {message}")
        
        try:
            chat_data = {
                'session_id': session_id,
                'message': message
            }
            
            response = requests.post(f"{BASE_URL}/api/chat/send", json=chat_data)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"   🤖 AI回复: {result['message']}")
                    print(f"   📊 准备生成: {result.get('ready_to_generate', False)}")
                    
                    if result.get('ready_to_generate'):
                        print(f"   ✅ 会话已准备好生成测试用例")
                        break
                else:
                    print(f"   ❌ 对话失败: {result.get('message')}")
            else:
                print(f"   ❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 对话请求异常: {e}")
        
        time.sleep(1)  # 避免请求过快
    
    # 步骤3: 生成测试用例
    print(f"\n🔄 步骤3: 生成测试用例")
    
    try:
        generate_data = {
            'session_id': session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/generation/generate", json=generate_data, stream=True)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   📡 接收流式响应:")
            test_cases = []
            
            for line in response.iter_lines():
                if line:
                    try:
                        # 解析流式响应
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # 移除 'data: ' 前缀
                            chunk = json.loads(data_str)
                            
                            chunk_type = chunk.get('type', 'unknown')
                            print(f"      📦 {chunk_type}: ", end="")
                            
                            if chunk_type == 'progress':
                                progress_data = chunk.get('data', {})
                                print(f"{progress_data.get('message', 'N/A')} ({progress_data.get('progress', 0)}%)")
                            elif chunk_type == 'complete':
                                complete_data = chunk.get('data', {})
                                test_cases = complete_data.get('test_cases', [])
                                print(f"生成完成，共 {len(test_cases)} 条测试用例")
                                break
                            elif chunk_type == 'error':
                                error_data = chunk.get('data', {})
                                print(f"生成失败: {error_data.get('message', 'N/A')}")
                                return False
                            else:
                                print(f"未知类型: {chunk}")
                                
                    except json.JSONDecodeError as e:
                        print(f"      ⚠️  解析响应失败: {e}")
                        continue
                        
            if test_cases:
                print(f"   ✅ 成功生成 {len(test_cases)} 条测试用例")
                
                # 显示生成的测试用例概要
                for i, tc in enumerate(test_cases[:3], 1):  # 只显示前3条
                    print(f"      {i}. {tc.get('name', 'N/A')} (ID: {tc.get('id', 'N/A')})")
                    
                if len(test_cases) > 3:
                    print(f"      ... 还有 {len(test_cases) - 3} 条测试用例")
            else:
                print(f"   ❌ 没有生成任何测试用例")
                return False
                
        else:
            print(f"   ❌ 生成请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 生成请求异常: {e}")
        return False
    
    # 步骤4: 确认并生成最终文件
    print(f"\n📄 步骤4: 确认并生成最终文件")
    
    try:
        finalize_data = {
            'session_id': session_id,
            'test_cases': test_cases
        }
        
        response = requests.post(f"{BASE_URL}/api/generation/finalize", json=finalize_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                file_id = result['file_id']
                print(f"   ✅ 文件生成成功")
                print(f"   📁 文件ID: {file_id}")
                print(f"   📊 测试用例数量: {result.get('test_cases_count', 'N/A')}")
            else:
                print(f"   ❌ 文件生成失败: {result.get('message')}")
                return False
        else:
            print(f"   ❌ 确认请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 确认请求异常: {e}")
        return False
    
    # 步骤5: 下载生成的文件
    print(f"\n⬇️  步骤5: 下载生成的文件")
    
    try:
        download_params = {
            'session_id': session_id,
            'file_id': file_id
        }
        
        response = requests.get(f"{BASE_URL}/api/generation/download", params=download_params)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 保存下载的文件
            filename = f"downloaded_test_cases_{session_id[:8]}.xml"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"   ✅ 文件下载成功")
            print(f"   📁 保存为: {filename}")
            print(f"   📊 文件大小: {file_size} 字节")
            
            # 显示文件内容的前几行
            print(f"   📄 文件内容预览:")
            content_preview = response.content.decode('utf-8')[:200]
            for line in content_preview.split('\n')[:3]:
                if line.strip():
                    print(f"      {line}")
            if len(content_preview) >= 200:
                print("      ...")
                
        else:
            print(f"   ❌ 下载请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 下载请求异常: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 完整流程测试成功！")
    print(f"📋 会话ID: {session_id}")
    print(f"📁 文件ID: {file_id}")
    print(f"📊 生成的测试用例数量: {len(test_cases)}")
    print("=" * 60)
    
    return True

def test_api_health():
    """测试API健康状态"""
    print("🏥 检查API健康状态")
    
    try:
        # 测试配置接口
        response = requests.get(f"{BASE_URL}/api/config/api-versions")
        if response.status_code == 200:
            print("   ✅ 配置接口正常")
        else:
            print(f"   ⚠️  配置接口异常: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ API健康检查失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("AI测试用例生成工具 - 完整流程测试")
    print("=" * 60)
    
    # 首先检查API健康状态
    if not test_api_health():
        print("❌ API健康检查失败，请检查服务器状态")
        exit(1)
    
    # 运行完整流程测试
    if test_complete_flow():
        print("\n✅ 所有测试通过！Mock数据工作正常。")
        exit(0)
    else:
        print("\n❌ 测试失败，请检查服务器日志。")
        exit(1)