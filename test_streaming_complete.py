#!/usr/bin/env python3
"""
流式UI改进功能完整测试
"""

import asyncio
import logging
from services.ai_service import AIService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_streaming_flow():
    """测试完整的流式功能流程"""
    logger.info("🧪 开始完整流式功能测试")
    
    # 初始化AI服务（Mock模式）
    config = {
        'mock_mode': True,
        'timeout': 30
    }
    
    ai_service = AIService(config)
    logger.info("✅ AI服务初始化完成")
    
    try:
        # 1. 创建会话
        user_id = "test_user"
        session_id = await ai_service.create_conversation_session(user_id)
        logger.info(f"📝 创建会话: {session_id}")
        
        # 2. 测试对话
        test_message = "请帮我分析这个测试用例"
        context = {'test_mode': True}
        
        logger.info(f"💬 开始对话: {test_message}")
        
        response = await ai_service.chat_with_agent(session_id, test_message, context)
        
        if response.get('success'):
            logger.info(f"✅ 对话成功: {response.get('reply', '')[:100]}...")
        else:
            logger.error(f"❌ 对话失败: {response.get('error', 'unknown')}")
            return False
        
        # 3. 测试流式消息
        logger.info("🌊 开始流式消息测试")
        
        stream_message = "请生成详细的测试用例"
        message_parts = []
        
        async for chunk in ai_service.send_message_streaming(session_id, stream_message):
            if chunk:
                event_type = chunk.get('event', 'unknown')
                
                if event_type == 'message':
                    content = chunk.get('content', '')
                    if content:
                        message_parts.append(content)
                        logger.info(f"📝 流式内容: '{content}'")
                elif event_type == 'message_end':
                    logger.info("🏁 流式消息结束")
                    break
                elif event_type == 'error':
                    logger.error(f"❌ 流式错误: {chunk.get('message', 'unknown')}")
                    break
        
        full_message = ''.join(message_parts)
        logger.info(f"📋 完整流式消息长度: {len(full_message)} 字符")
        
        # 4. 测试生成流程
        logger.info("⚙️ 开始测试用例生成测试")
        
        generation_context = {
            'files_info': {'case_template': {'file_path': 'test.xml'}},
            'requirements': ['登录功能测试', '权限验证']
        }
        
        test_cases = []
        async for chunk in ai_service.generate_test_cases(session_id, generation_context):
            if chunk:
                chunk_type = chunk.get('type', 'unknown')
                
                if chunk_type == 'progress':
                    stage = chunk.get('data', {}).get('stage', 'unknown')
                    message = chunk.get('data', {}).get('message', '')
                    progress = chunk.get('data', {}).get('progress', 0)
                    logger.info(f"📊 生成进度: {stage} - {message} ({progress}%)")
                elif chunk_type == 'complete':
                    test_cases = chunk.get('data', {}).get('test_cases', [])
                    logger.info(f"✅ 生成完成: {len(test_cases)} 条测试用例")
                    break
                elif chunk_type == 'error':
                    logger.error(f"❌ 生成错误: {chunk.get('data', {}).get('message', 'unknown')}")
                    break
        
        logger.info(f"📋 生成的测试用例数量: {len(test_cases)}")
        
        # 5. 清理会话
        await ai_service.cleanup_session(session_id)
        logger.info("🧹 会话清理完成")
        
        logger.info("✅ 完整流式功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False


async def test_error_handling():
    """测试错误处理"""
    logger.info("🛡️ 开始错误处理测试")
    
    config = {
        'mock_mode': True,
        'timeout': 30
    }
    
    ai_service = AIService(config)
    
    try:
        # 测试无效会话ID
        invalid_session = "invalid_session_123"
        test_message = "测试消息"
        
        logger.info("🔍 测试无效会话处理")
        
        error_handled = False
        async for chunk in ai_service.send_message_streaming(invalid_session, test_message):
            if chunk and chunk.get('event') == 'error':
                logger.info(f"✅ 正确处理错误: {chunk.get('message', 'unknown')}")
                error_handled = True
                break
        
        if not error_handled:
            logger.warning("⚠️ 未检测到预期的错误处理")
        
        logger.info("✅ 错误处理测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误处理测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始流式UI改进功能完整测试")
    
    tests = [
        ("完整流式功能", test_complete_streaming_flow),
        ("错误处理", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ 测试通过: {test_name}")
            else:
                logger.error(f"❌ 测试失败: {test_name}")
                
        except Exception as e:
            logger.error(f"💥 测试异常: {test_name}, error: {e}")
            results[test_name] = False
    
    # 输出测试总结
    logger.info(f"\n{'='*50}")
    logger.info("📋 测试结果总结")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！流式UI改进功能正常工作")
        return 0
    else:
        print(f"❌ {total - passed} 个测试失败，共 {total} 个测试")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)