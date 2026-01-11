#!/usr/bin/env python3
"""
测试Dify连接和ChatFlow对接的脚本
"""

import asyncio
import logging
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_dify_connection():
    """测试Dify基础连接"""
    print("=== 测试Dify基础连接 ===")
    
    # 创建AI服务配置（关闭Mock模式）
    config = Config.AI_SERVICE_CONFIG.copy()
    config['mock_mode'] = False  # 确保使用Dify模式
    
    print(f"配置信息:")
    print(f"  - Dify URL: {config['dify_url']}")
    print(f"  - Mock模式: {config['mock_mode']}")
    print(f"  - 流式模式: {config['stream_mode']}")
    
    ai_service = AIService(config)
    
    # 测试健康检查
    print("\n1. 执行健康检查...")
    health = ai_service.health_check()
    print(f"健康状态: {json.dumps(health, indent=2, ensure_ascii=False)}")
    
    if health['status'] != 'healthy':
        print("❌ 健康检查失败，请检查Dify配置")
        return False
    
    return True


async def test_dify_chat():
    """测试Dify对话功能"""
    print("\n=== 测试Dify对话功能 ===")
    
    # 创建AI服务
    config = Config.AI_SERVICE_CONFIG.copy()
    config['mock_mode'] = False
    ai_service = AIService(config)
    
    # 创建测试会话
    print("\n1. 创建测试会话...")
    session_id = await ai_service.create_conversation_session("test_user")
    print(f"会话ID: {session_id}")
    
    # 测试简单对话
    print("\n2. 发送测试消息...")
    test_message = "你好，我想测试一下对话功能"
    context = {
        'test_mode': True,
        'user_id': 'test_user'
    }
    
    try:
        response = await ai_service.chat_with_agent(session_id, test_message, context)
        print(f"AI回复: {json.dumps(response, indent=2, ensure_ascii=False)}")
        
        if response.get('reply'):
            print("✅ 对话测试成功")
            return True
        else:
            print("❌ 对话测试失败：没有收到回复")
            return False
            
    except Exception as e:
        print(f"❌ 对话测试异常: {str(e)}")
        return False


async def test_dify_file_analysis():
    """测试Dify文件分析功能"""
    print("\n=== 测试Dify文件分析功能 ===")
    
    config = Config.AI_SERVICE_CONFIG.copy()
    config['mock_mode'] = False
    ai_service = AIService(config)
    
    # 模拟文件信息
    files_info = {
        'case_template': {
            'filename': 'test_template.xml',
            'size': 1024,
            'type': 'xml'
        }
    }
    
    print("\n1. 执行文件分析...")
    try:
        # 使用异步版本进行测试
        result = await ai_service.analyze_files_async(files_info)
        print(f"分析结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('template_info'):
            print("✅ 文件分析测试成功")
            return True
        else:
            print("❌ 文件分析测试失败：没有收到分析结果")
            return False
            
    except Exception as e:
        print(f"❌ 文件分析测试异常: {str(e)}")
        return False


async def test_dify_stream_generation():
    """测试Dify流式生成功能"""
    print("\n=== 测试Dify流式生成功能 ===")
    
    config = Config.AI_SERVICE_CONFIG.copy()
    config['mock_mode'] = False
    ai_service = AIService(config)
    
    # 创建测试会话
    session_id = await ai_service.create_conversation_session("test_user")
    
    # 测试流式生成
    print("\n1. 开始流式生成测试...")
    context = {
        'test_scenario': 'login',
        'user_requirements': '生成用户登录功能的测试用例'
    }
    
    try:
        stream_count = 0
        async for data in ai_service.generate_test_cases(session_id, context):
            stream_count += 1
            print(f"流式数据 #{stream_count}: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 限制输出数量，避免过多日志
            if stream_count >= 5:
                print("... (限制输出，继续接收数据)")
                break
        
        if stream_count > 0:
            print("✅ 流式生成测试成功")
            return True
        else:
            print("❌ 流式生成测试失败：没有收到流式数据")
            return False
            
    except Exception as e:
        print(f"❌ 流式生成测试异常: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("开始测试Dify ChatFlow对接")
    print("=" * 50)
    
    success_count = 0
    total_tests = 4
    
    # 测试1: 基础连接
    if await test_dify_connection():
        success_count += 1
    
    # 测试2: 对话功能
    if await test_dify_chat():
        success_count += 1
    
    # 测试3: 文件分析
    if await test_dify_file_analysis():
        success_count += 1
    
    # 测试4: 流式生成
    if await test_dify_stream_generation():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 项测试通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！Dify ChatFlow对接成功")
    elif success_count > 0:
        print("⚠️  部分测试通过，请检查失败的功能")
    else:
        print("❌ 所有测试失败，请检查Dify配置和网络连接")
    
    return success_count == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)