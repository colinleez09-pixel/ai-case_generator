#!/usr/bin/env python3
"""
测试错误处理和降级机制的脚本
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService, DifyErrorHandler, CircuitBreaker, ModeSelector
from config import Config
import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_error_handler():
    """测试错误处理器"""
    print("=== 测试错误处理器 ===")
    
    # 创建模式选择器和错误处理器
    config = {'mock_mode': False, 'dify_config': {}}
    mode_selector = ModeSelector(config)
    error_handler = DifyErrorHandler(mode_selector)
    
    # 测试客户端错误处理
    print("\n1. 测试客户端错误处理 (401 Unauthorized)")
    
    # 创建一个模拟的请求信息对象
    class MockRequestInfo:
        def __init__(self):
            self.real_url = "https://api.dify.ai/v1/chat-messages"
            self.method = "POST"
            self.headers = {}
    
    client_error = aiohttp.ClientResponseError(
        request_info=MockRequestInfo(),
        history=(),
        status=401,
        message="Unauthorized"
    )
    
    result = await error_handler.handle_api_error(client_error, "test_req_1", "chat")
    print(f"处理结果: {result}")
    assert result['error_type'] == 'client_error'
    assert result['should_retry'] == False
    
    # 测试服务器错误重试
    print("\n2. 测试服务器错误重试 (500 Internal Server Error)")
    server_error = aiohttp.ClientResponseError(
        request_info=MockRequestInfo(),
        history=(),
        status=500,
        message="Internal Server Error"
    )
    
    # 第一次重试
    result = await error_handler.handle_api_error(server_error, "test_req_2", "chat")
    print(f"第1次重试结果: {result}")
    assert result['should_retry'] == True
    assert result['retry_attempt'] == 1
    
    # 第二次重试
    result = await error_handler.handle_api_error(server_error, "test_req_2", "chat")
    print(f"第2次重试结果: {result}")
    assert result['should_retry'] == True
    assert result['retry_attempt'] == 2
    
    # 第三次重试
    result = await error_handler.handle_api_error(server_error, "test_req_2", "chat")
    print(f"第3次重试结果: {result}")
    assert result['should_retry'] == True
    assert result['retry_attempt'] == 3
    
    # 第四次应该降级
    result = await error_handler.handle_api_error(server_error, "test_req_2", "chat")
    print(f"第4次（降级）结果: {result}")
    assert result['fallback_to_mock'] == True
    
    # 测试超时错误
    print("\n3. 测试超时错误处理")
    timeout_error = asyncio.TimeoutError("Request timeout")
    result = await error_handler.handle_api_error(timeout_error, "test_req_3", "upload")
    print(f"超时错误处理结果: {result}")
    assert result['should_retry'] == True
    
    # 测试连接错误（立即降级）
    print("\n4. 测试连接错误处理")
    connection_error = aiohttp.ClientConnectionError("Connection failed")
    result = await error_handler.handle_api_error(connection_error, "test_req_4", "generate")
    print(f"连接错误处理结果: {result}")
    assert result['fallback_to_mock'] == True
    
    print("✅ 错误处理器测试通过")


async def test_circuit_breaker():
    """测试熔断器"""
    print("\n=== 测试熔断器 ===")
    
    # 创建熔断器（失败阈值=3，超时=5秒）
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=5, success_threshold=2)
    
    async def failing_operation():
        """总是失败的操作"""
        raise Exception("Operation failed")
    
    async def successful_operation():
        """总是成功的操作"""
        return "success"
    
    # 测试正常状态
    print("\n1. 测试熔断器初始状态")
    state = circuit_breaker.get_state()
    print(f"初始状态: {state}")
    assert state['state'] == 'CLOSED'
    
    # 测试失败累积
    print("\n2. 测试失败累积")
    for i in range(3):
        try:
            await circuit_breaker.call(failing_operation)
        except Exception as e:
            print(f"第{i+1}次失败: {str(e)}")
    
    state = circuit_breaker.get_state()
    print(f"3次失败后状态: {state}")
    assert state['state'] == 'OPEN'
    
    # 测试熔断器打开状态
    print("\n3. 测试熔断器打开状态")
    try:
        await circuit_breaker.call(successful_operation)
        assert False, "应该抛出熔断器打开异常"
    except Exception as e:
        print(f"熔断器阻止调用: {str(e)}")
        assert "熔断器处于打开状态" in str(e)
    
    # 等待超时后测试半开状态
    print("\n4. 等待超时后测试半开状态")
    await asyncio.sleep(6)  # 等待超过超时时间
    
    # 第一次成功调用
    result = await circuit_breaker.call(successful_operation)
    print(f"半开状态第1次成功调用: {result}")
    
    state = circuit_breaker.get_state()
    print(f"第1次成功后状态: {state}")
    assert state['state'] == 'HALF_OPEN'
    
    # 第二次成功调用，应该关闭熔断器
    result = await circuit_breaker.call(successful_operation)
    print(f"半开状态第2次成功调用: {result}")
    
    state = circuit_breaker.get_state()
    print(f"第2次成功后状态: {state}")
    assert state['state'] == 'CLOSED'
    
    print("✅ 熔断器测试通过")


async def test_ai_service_integration():
    """测试AI服务集成"""
    print("\n=== 测试AI服务集成 ===")
    
    # 创建AI服务配置
    config = Config.AI_SERVICE_CONFIG.copy()
    config['mock_mode'] = True  # 使用Mock模式进行测试
    
    ai_service = AIService(config)
    
    # 测试健康检查
    print("\n1. 测试健康检查")
    health = ai_service.health_check()
    print(f"健康状态: {health}")
    assert health['status'] == 'healthy'
    assert health['mode'] == 'mock'
    
    # 测试服务统计
    print("\n2. 测试服务统计")
    stats = ai_service.get_service_stats()
    print(f"服务统计: {stats}")
    assert 'error_handler_stats' in stats
    assert 'circuit_breaker_state' in stats
    
    # 测试错误处理重置
    print("\n3. 测试错误处理重置")
    ai_service.reset_error_handling()
    print("错误处理状态已重置")
    
    # 测试模式切换
    print("\n4. 测试模式切换")
    await ai_service.switch_mode('mock', 'test')
    assert ai_service.mode_selector.current_mode == 'mock'
    print("模式切换测试完成")
    
    print("✅ AI服务集成测试通过")


async def main():
    """主测试函数"""
    print("开始测试Dify集成错误处理和降级机制")
    print("=" * 50)
    
    try:
        await test_error_handler()
        await test_circuit_breaker()
        await test_ai_service_integration()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！错误处理和降级机制实现成功")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())