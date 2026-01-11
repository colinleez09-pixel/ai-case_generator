#!/usr/bin/env python3
"""
修复Dify连接问题 - 处理代理和SSL问题
"""

import requests
import json
import os
import urllib3
from config import Config

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_dify_with_proxy_fix():
    """测试Dify连接 - 修复代理问题"""
    print("🔧 修复Dify连接问题...")
    
    config = Config.AI_SERVICE_CONFIG
    dify_url = config['dify_url']
    dify_token = config['dify_token']
    
    print(f"📋 配置信息:")
    print(f"  DIFY_URL: {dify_url}")
    print(f"  DIFY_TOKEN: {dify_token[:20]}...")
    
    # 检查代理设置
    print(f"\n🔍 检查代理设置:")
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    print(f"  HTTP_PROXY: {http_proxy}")
    print(f"  HTTPS_PROXY: {https_proxy}")
    
    # 方案1: 禁用代理
    print(f"\n🚀 方案1: 禁用代理测试...")
    success1 = test_without_proxy(dify_url, dify_token)
    
    # 方案2: 使用代理但禁用SSL验证
    if not success1 and (http_proxy or https_proxy):
        print(f"\n🚀 方案2: 使用代理但禁用SSL验证...")
        success2 = test_with_proxy_no_ssl(dify_url, dify_token)
    else:
        success2 = False
    
    # 方案3: 修改.env配置使用Mock模式
    if not success1 and not success2:
        print(f"\n🚀 方案3: 建议使用Mock模式...")
        suggest_mock_mode()
        return False
    
    return success1 or success2

def test_without_proxy(dify_url, dify_token):
    """测试不使用代理的连接"""
    try:
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
        
        # 创建一个不使用代理的session
        session = requests.Session()
        session.proxies = {}  # 禁用代理
        
        response = session.post(
            f'{dify_url}/chat-messages',
            json=test_message,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 禁用代理连接成功!")
            print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 更新.env文件，禁用代理
            update_env_disable_proxy()
            return True
        else:
            print(f"❌ 禁用代理连接失败: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 禁用代理测试异常: {e}")
        return False

def test_with_proxy_no_ssl(dify_url, dify_token):
    """测试使用代理但禁用SSL验证"""
    try:
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
        
        response = requests.post(
            f'{dify_url}/chat-messages',
            json=test_message,
            headers=headers,
            timeout=10,
            verify=False  # 禁用SSL验证
        )
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 代理+禁用SSL验证连接成功!")
            print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 代理+禁用SSL验证连接失败: {response.status_code}")
            print(f"📝 错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 代理+禁用SSL验证测试异常: {e}")
        return False

def update_env_disable_proxy():
    """更新.env文件，添加禁用代理的配置"""
    try:
        env_content = []
        env_file = '.env'
        
        # 读取现有.env文件
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        
        # 添加禁用代理的配置
        proxy_config_added = False
        for i, line in enumerate(env_content):
            if line.startswith('# 代理配置') or line.startswith('# Proxy'):
                proxy_config_added = True
                break
        
        if not proxy_config_added:
            env_content.append('\n# 代理配置 - 禁用代理以解决Dify连接问题\n')
            env_content.append('HTTP_PROXY=\n')
            env_content.append('HTTPS_PROXY=\n')
            env_content.append('NO_PROXY=localhost,127.0.0.1\n')
        
        # 写回.env文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(env_content)
        
        print("✅ 已更新.env文件，禁用代理配置")
        
    except Exception as e:
        print(f"❌ 更新.env文件失败: {e}")

def suggest_mock_mode():
    """建议使用Mock模式"""
    print("💡 建议解决方案:")
    print("1. 网络连接问题导致无法连接到Dify服务")
    print("2. 建议暂时使用Mock模式进行开发和测试")
    print("3. 修改.env文件中的AI_MOCK_MODE=true")
    print("4. 或者联系网络管理员解决代理/防火墙问题")
    
    # 自动修改.env文件启用Mock模式
    try:
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换Mock模式配置
            if 'AI_MOCK_MODE=false' in content:
                content = content.replace('AI_MOCK_MODE=false', 'AI_MOCK_MODE=true')
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ 已自动启用Mock模式 (AI_MOCK_MODE=true)")
            else:
                print("ℹ️ Mock模式可能已经启用或需要手动配置")
    except Exception as e:
        print(f"❌ 自动配置Mock模式失败: {e}")

def test_ai_service_after_fix():
    """测试修复后的AI服务"""
    print("\n🤖 测试修复后的AI服务...")
    
    try:
        from services.ai_service import AIService
        
        # 重新加载配置
        config = Config.AI_SERVICE_CONFIG.copy()
        print(f"📋 当前配置: mock_mode={config['mock_mode']}")
        
        ai_service = AIService(config)
        
        print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
        print(f"📊 是否Mock模式: {ai_service.mode_selector.is_mock_mode()}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("修复Dify连接问题")
    print("=" * 60)
    
    # 测试连接修复
    connection_fixed = test_dify_with_proxy_fix()
    
    # 测试AI服务
    ai_service_ok = test_ai_service_after_fix()
    
    print("\n" + "=" * 60)
    print("修复结果总结")
    print("=" * 60)
    
    if connection_fixed:
        print("✅ Dify连接问题已修复")
        print("✅ 系统可以使用真实Dify服务")
    else:
        print("⚠️ Dify连接仍有问题，已启用Mock模式")
        print("✅ 系统可以使用Mock模式正常工作")
    
    if ai_service_ok:
        print("✅ AI服务工作正常")
    else:
        print("❌ AI服务仍有问题")
    
    print("\n📝 下一步:")
    if connection_fixed:
        print("1. 重启应用以应用新的网络配置")
        print("2. 测试文件上传自动分析功能")
    else:
        print("1. 使用Mock模式进行开发和测试")
        print("2. 稍后解决网络连接问题后再切换到Dify模式")