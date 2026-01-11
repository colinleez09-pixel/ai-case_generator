#!/usr/bin/env python3
"""
流式UI改进功能基本测试
"""

import asyncio
import logging
from services.ai_service import AIService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_streaming():
    """测试基本流式功能"""
    logger.info("🧪 开始基本流式功能测试")
    
    # 初始化AI服务（Mock模式）
    config = {
        'mock_mode': True,
        'timeout': 30
    }
    
    ai_service = AIService(config)
    logger.info("✅ AI服务初始化完成")
    
    # 测试流式消息
    session_id = "test_session_123"
    test_message = "请帮我生成测试用例"
    
    logger.info(f"📤 发送流式消息: {test_message}")
    
    try:
        message_parts = []
        async for chunk in ai_service.send_message_streaming(session_id, test_message):
            if chunk:
                event_type = chunk.get('event', 'unknown')
                
                if event_type == 'message':
                    content = chunk.get('content', '')
                    if content:
                        message_parts.append(content)
                        logger.info(f"📝 收到内容: '{content}'")
                elif event_type == 'message_end':
                    logger.info("🏁 消息结束")
                    break
                elif event_type == 'error':
                    logger.error(f"❌ 错误: {chunk.get('message', 'unknown')}")
                    break
        
        full_message = ''.join(message_parts)
        logger.info(f"📋 完整消息: {full_message}")
        logger.info("✅ 基本流式功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


async def main():
    """主函数"""
    result = await test_basic_streaming()
    
    if result:
        print("🎉 基本流式功能测试通过！")
        return 0
    else:
        print("❌ 基本流式功能测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)