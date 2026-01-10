#!/usr/bin/env python3
"""
Mock数据验证脚本
专门用于验证AI服务的Mock数据生成功能
"""

import requests
import json
import time
from io import BytesIO

BASE_URL = "http://localhost:5000"

def create_simple_test_file():
    """创建简单的测试XML文件"""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="示例测试用例">
        <steps>
            <step>执行测试步骤</step>
        </steps>
    </testcase>
</testcases>"""
    return BytesIO(content.encode('utf-8'))

def verify_mock_data():
    """验证Mock数据生成"""
    print("🔍 验证Mock数据生成功能")
    print("=" * 50)
    
    # 1. 启动任务
    print("\n📁 启动生成任务...")
    files = {
        'case_template': ('test.xml', create_simple_test_file(), 'application/xml')
    }
    
    response = requests.post(f"{BASE_URL}/api/generation/start", files=files)
    if response.status_code != 200:
        print(f"❌ 启动失败: {response.text}")
        return False
    
    result = response.json()
    session_id = result['session_id']
    print(f"✅ 任务启动成功，会话ID: {session_id}")
    
    # 2. 触发生成
    print("\n💬 发送生成指令...")
    chat_data = {
        'session_id': session_id,
        'message': '开始生成'
    }
    
    response = requests.post(f"{BASE_URL}/api/chat/send", json=chat_data)
    if response.status_code != 200:
        print(f"❌ 对话失败: {response.text}")
        return False
    
    result = response.json()
    if not result.get('ready_to_generate'):
        print(f"❌ 会话未准备好生成")
        return False
    
    print(f"✅ 会话已准备好生成")
    
    # 3. 生成测试用例
    print("\n🔄 生成测试用例...")
    generate_data = {'session_id': session_id}
    
    response = requests.post(f"{BASE_URL}/api/generation/generate", json=generate_data, stream=True)
    if response.status_code != 200:
        print(f"❌ 生成失败: {response.text}")
        return False
    
    test_cases = []
    for line in response.iter_lines():
        if line:
            try:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    chunk = json.loads(data_str)
                    
                    if chunk.get('type') == 'complete':
                        test_cases = chunk.get('data', {}).get('test_cases', [])
                        break
                        
            except json.JSONDecodeError:
                continue
    
    if not test_cases:
        print("❌ 没有生成测试用例")
        return False
    
    print(f"✅ 成功生成 {len(test_cases)} 条测试用例")
    
    # 4. 验证Mock数据质量
    print("\n🔍 验证Mock数据质量...")
    
    # 检查第一个测试用例的结构
    if len(test_cases) > 0:
        tc = test_cases[0]
        
        # 验证基本字段
        required_fields = ['id', 'name', 'preconditions', 'steps', 'expectedResults']
        for field in required_fields:
            if field not in tc:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        print(f"✅ 测试用例结构完整")
        
        # 验证预置条件
        preconditions = tc.get('preconditions', [])
        if preconditions and len(preconditions) > 0:
            pre = preconditions[0]
            if 'components' in pre and len(pre['components']) > 0:
                comp = pre['components'][0]
                if 'type' in comp and 'name' in comp and 'params' in comp:
                    print(f"✅ 预置条件组件结构正确")
                else:
                    print(f"❌ 预置条件组件结构不完整")
                    return False
        
        # 验证测试步骤
        steps = tc.get('steps', [])
        if steps and len(steps) > 0:
            step = steps[0]
            if 'components' in step and len(step['components']) > 0:
                comp = step['components'][0]
                if 'type' in comp and 'name' in comp and 'params' in comp:
                    print(f"✅ 测试步骤组件结构正确")
                else:
                    print(f"❌ 测试步骤组件结构不完整")
                    return False
        
        # 验证预期结果
        expected_results = tc.get('expectedResults', [])
        if expected_results and len(expected_results) > 0:
            result = expected_results[0]
            if 'components' in result and len(result['components']) > 0:
                comp = result['components'][0]
                if 'type' in comp and 'name' in comp and 'params' in comp:
                    print(f"✅ 预期结果组件结构正确")
                else:
                    print(f"❌ 预期结果组件结构不完整")
                    return False
    
    # 5. 验证不同类型的组件
    print("\n🧩 验证组件类型多样性...")
    
    all_components = []
    for tc in test_cases:
        # 收集所有组件
        for pre in tc.get('preconditions', []):
            all_components.extend(pre.get('components', []))
        for step in tc.get('steps', []):
            all_components.extend(step.get('components', []))
        for result in tc.get('expectedResults', []):
            all_components.extend(result.get('components', []))
    
    component_types = set(comp.get('type') for comp in all_components)
    print(f"✅ 发现组件类型: {', '.join(component_types)}")
    
    # 验证是否包含常见的组件类型
    expected_types = {'api', 'input', 'button', 'assert'}
    if expected_types.issubset(component_types):
        print(f"✅ 包含所有预期的组件类型")
    else:
        missing = expected_types - component_types
        print(f"⚠️  缺少组件类型: {', '.join(missing)}")
    
    print("\n" + "=" * 50)
    print("🎉 Mock数据验证完成！")
    print(f"📊 生成的测试用例数量: {len(test_cases)}")
    print(f"🧩 组件类型数量: {len(component_types)}")
    print(f"📦 总组件数量: {len(all_components)}")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    print("AI测试用例生成工具 - Mock数据验证")
    print("=" * 50)
    
    try:
        if verify_mock_data():
            print("\n✅ Mock数据验证通过！")
            exit(0)
        else:
            print("\n❌ Mock数据验证失败！")
            exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程中发生异常: {e}")
        exit(1)