#!/usr/bin/env python3
"""
简单的Dify连接测试
"""

# 使用正常代理设置连接Dify
print("🔧 使用正常代理设置连接Dify")

import requests
import json
from config import Config

def test_simple_dify_connection():
    """简单测试Dify连接"""
    print("🔗 测试Dify连接...")
    
    config = Config.AI_SERVICE_CONFIG
    dify_url = config['dify_url']
    dify_token = config['dify_token']
    
    print(f"📋 配置信息:")
    print(f"  DIFY_URL: {dify_url}")
    print(f"  DIFY_TOKEN: {dify_token[:20]}...")
    print(f"  MOCK_MODE: {config['mock_mode']}")
    
    # 测试基本连接
    headers = {
        'Authorization': f'Bearer {dify_token}',
        'Content-Type': 'application/json'
    }
    
    test_message = {
        'inputs': {},
        'query': '测试连接',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    try:
        print("🚀 发送测试请求到Dify...")
        
        response = requests.post(
            f'{dify_url}/chat-messages',
            json=test_message,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify连接成功!")
            print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_text = response.text
            print(f"❌ Dify连接失败: {response.status_code}")
            print(f"📝 错误内容: {error_text}")
            return False
                    
    except requests.exceptions.Timeout as e:
        print(f"❌ Dify连接超时: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Dify连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("简单Dify连接测试")
    print("=" * 60)
    
    success = test_simple_dify_connection()
    
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    
    if success:
        print("✅ Dify连接测试成功")
    else:
        print("❌ Dify连接测试失败")
        print("\n🔧 可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 验证DIFY_TOKEN是否正确")
        print("3. 确认Dify服务是否可用")
        print("4. 检查防火墙或代理设置")