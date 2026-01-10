#!/usr/bin/env python3
"""
简单的应用测试脚本
"""

import requests
import json
import sys

def test_health_endpoint():
    """测试健康检查端点"""
    try:
        response = requests.get('http://127.0.0.1:5000/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 健康检查通过: {data}")
            return True
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")
        return False

def test_config_endpoints():
    """测试配置端点"""
    endpoints = [
        '/api/config/api-versions',
        '/api/config/preset-steps', 
        '/api/config/preset-components',
        '/api/config/all'
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://127.0.0.1:5000{endpoint}')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✓ {endpoint} 正常")
                    results.append(True)
                else:
                    print(f"✗ {endpoint} 返回失败: {data.get('message')}")
                    results.append(False)
            else:
                print(f"✗ {endpoint} HTTP错误: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"✗ {endpoint} 异常: {e}")
            results.append(False)
    
    return all(results)

def test_chat_endpoint():
    """测试聊天端点错误处理"""
    try:
        # 测试缺少数据的情况
        response = requests.post('http://127.0.0.1:5000/api/chat/send')
        if response.status_code == 400:
            print("✓ 聊天端点错误处理正常")
            return True
        else:
            print(f"✗ 聊天端点错误处理异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 聊天端点测试异常: {e}")
        return False

def test_generation_endpoint():
    """测试生成端点错误处理"""
    try:
        # 测试缺少文件的情况
        response = requests.post('http://127.0.0.1:5000/api/generation/start')
        if response.status_code == 400:
            print("✓ 生成端点错误处理正常")
            return True
        else:
            print(f"✗ 生成端点错误处理异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 生成端点测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试AI测试用例生成工具...")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health_endpoint),
        ("配置端点", test_config_endpoints),
        ("聊天端点", test_chat_endpoint),
        ("生成端点", test_generation_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n测试 {test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有测试通过! ({passed}/{total})")
        return 0
    else:
        print(f"❌ 部分测试失败: {passed}/{total}")
        return 1

if __name__ == "__main__":
    sys.exit(main())