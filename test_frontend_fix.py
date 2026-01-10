#!/usr/bin/env python3
"""
测试前端修复 - 验证Mock数据能正确显示在前端
"""

import requests
import json
import time

def test_frontend_mock_data():
    """测试前端Mock数据显示"""
    base_url = "http://localhost:5000/api"
    
    print("🧪 测试前端Mock数据显示")
    print("=" * 50)
    
    # 1. 启动生成任务
    print("📁 步骤1: 启动生成任务")
    
    # 创建测试文件
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <steps>
            <step>打开登录页面</step>
        </steps>
    </testcase>
</testcases>"""
    
    files = {
        'case_template': ('test.xml', test_xml, 'application/xml')
    }
    data = {
        'config': json.dumps({'api_version': 'v1.0'})
    }
    
    response = requests.post(f"{base_url}/generation/start", files=files, data=data)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 启动失败: {response.text}")
        return False
    
    result = response.json()
    session_id = result['session_id']
    print(f"   ✅ 会话ID: {session_id}")
    
    # 2. 进行对话直到准备生成
    print("\n💬 步骤2: 对话交互")
    
    # 发送"开始生成"消息
    chat_data = {
        'session_id': session_id,
        'message': '开始生成'
    }
    
    response = requests.post(f"{base_url}/chat/send", json=chat_data)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 对话失败: {response.text}")
        return False
    
    result = response.json()
    print(f"   🤖 AI回复: {result['message'][:50]}...")
    print(f"   📊 准备生成: {result.get('ready_to_generate', False)}")
    
    # 3. 生成测试用例
    print("\n🔄 步骤3: 生成测试用例")
    
    gen_data = {
        'session_id': session_id
    }
    
    response = requests.post(f"{base_url}/generation/generate", json=gen_data, stream=True)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ 生成失败: {response.text}")
        return False
    
    # 解析流式响应
    test_cases = []
    progress_count = 0
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    
                    if data.get('type') == 'progress':
                        progress_count += 1
                        progress_data = data.get('data', {})
                        progress = progress_data.get('progress', 0)
                        message = progress_data.get('message', 'N/A')
                        print(f"      📦 进度 {progress_count}: {message} ({progress}%)")
                        
                    elif data.get('type') == 'complete':
                        complete_data = data.get('data', {})
                        test_cases = complete_data.get('test_cases', [])
                        total_count = complete_data.get('total_count', 0)
                        print(f"      📦 完成: 共生成 {total_count} 条测试用例")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"      ⚠️  解析失败: {e}")
                    continue
    
    # 4. 验证结果
    print(f"\n📊 步骤4: 验证结果")
    print(f"   进度更新次数: {progress_count}")
    print(f"   生成的测试用例数量: {len(test_cases)}")
    
    if len(test_cases) > 0:
        print("   ✅ Mock数据生成成功！")
        print("   📋 测试用例列表:")
        for i, tc in enumerate(test_cases, 1):
            print(f"      {i}. {tc.get('name', 'N/A')} (ID: {tc.get('id', 'N/A')})")
            
        # 验证数据结构
        first_tc = test_cases[0]
        required_fields = ['id', 'name', 'preconditions', 'steps', 'expectedResults']
        missing_fields = [field for field in required_fields if field not in first_tc]
        
        if missing_fields:
            print(f"   ⚠️  缺少字段: {missing_fields}")
        else:
            print("   ✅ 数据结构完整")
            
        return True
    else:
        print("   ❌ 没有生成测试用例")
        return False

if __name__ == "__main__":
    success = test_frontend_mock_data()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 前端Mock数据测试成功！")
        print("💡 现在前端应该能正确显示 '共 3 个用例' 而不是 '共 0 个用例'")
    else:
        print("❌ 前端Mock数据测试失败")
    print("=" * 50)