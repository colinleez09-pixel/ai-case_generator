#!/usr/bin/env python3
"""
修复Dify代理连接问题
"""

import os
import requests
import json
from config import Config

def disable_proxy_for_dify():
    """禁用代理以连接Dify"""
    print("🔧 禁用代理设置...")
    
    # 临时禁用代理环境变量
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    original_proxies = {}
    
    for var in proxy_vars:
        if var in os.environ:
            original_proxies[var] = os.environ[var]
            del os.environ[var]
            print(f"  已禁用: {var}")
    
    return original_proxies

def test_dify_direct_connection():
    """测试直接连接Dify"""
    print("🚀 测试直接连接Dify...")
    
    config = Config.AI_SERVICE_CONFIG
    dify_url = config['dify_url']
    dify_token = config['dify_token']
    
    headers = {
        'Authorization': f'Bearer {dify_token}',
        'Content-Type': 'application/json'
    }
    
    test_message = {
        'inputs': {},
        'query': '你好，这是一个连接测试',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    try:
        # 创建一个明确禁用代理的session
        session = requests.Session()
        session.proxies = {}  # 明确禁用代理
        session.trust_env = False  # 不信任环境变量中的代理设置
        
        response = session.post(
            f'{dify_url}/chat-messages',
            json=test_message,
            headers=headers,
            timeout=15,
            verify=True  # 启用SSL验证
        )
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify连接成功!")
            print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Dify连接失败: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False

def patch_requests_for_dify():
    """为整个应用打补丁，禁用代理"""
    print("🔧 为应用打补丁，禁用代理...")
    
    # 修改requests的默认行为
    import requests.adapters
    
    original_send = requests.adapters.HTTPAdapter.send
    
    def patched_send(self, request, **kwargs):
        # 对Dify API请求禁用代理
        if 'api.dify.ai' in request.url:
            kwargs['proxies'] = {}
            print(f"🔧 对Dify请求禁用代理: {request.url}")
        return original_send(self, request, **kwargs)
    
    requests.adapters.HTTPAdapter.send = patched_send
    print("✅ 代理补丁已应用")

def update_ai_service_for_direct_connection():
    """更新AI服务以支持直接连接"""
    print("🔧 更新AI服务配置...")
    
    # 创建一个临时的配置文件
    patch_content = '''
# 临时补丁：禁用代理连接Dify
import os
import requests

# 禁用代理环境变量
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

# 修改requests默认行为
original_request = requests.request

def patched_request(*args, **kwargs):
    if len(args) > 1 and 'api.dify.ai' in str(args[1]):
        kwargs['proxies'] = {}
        kwargs['verify'] = True
    return original_request(*args, **kwargs)

requests.request = patched_request
print("🔧 Dify连接补丁已加载")
'''
    
    with open('dify_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ 补丁文件已创建: dify_patch.py")

def main():
    """主函数"""
    print("=" * 60)
    print("修复Dify代理连接问题")
    print("=" * 60)
    
    # 1. 禁用代理
    original_proxies = disable_proxy_for_dify()
    
    # 2. 测试直接连接
    connection_success = test_dify_direct_connection()
    
    if connection_success:
        print("\n✅ Dify连接成功！")
        
        # 3. 创建补丁
        update_ai_service_for_direct_connection()
        
        print("\n📝 下一步:")
        print("1. 重启Flask应用")
        print("2. 测试文件上传自动分析功能")
        print("3. 验证真实Dify对话")
        
        return True
    else:
        print("\n❌ Dify连接仍然失败")
        print("📝 可能的原因:")
        print("1. 网络防火墙阻止连接")
        print("2. DIFY_TOKEN无效")
        print("3. Dify服务不可用")
        
        # 恢复代理设置
        for var, value in original_proxies.items():
            os.environ[var] = value
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)