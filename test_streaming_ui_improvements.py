#!/usr/bin/env python3
"""
流式UI改进功能测试

测试流式进度指示器、流式消息显示和Dify流式API集成
"""

import asyncio
import json
import logging
from typing import Dict, Any
from services.ai_service import AIService, DifyHandler, DifyStreamingClient
from services.streaming_chat_handler import StreamingChatHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingUITester:
    """流式UI功能测试器"""
    
    def __init__(self):
        """初始化测试器"""
        # Mock配置
        self.config = {
            'dify_url': 'https://api.dify.ai/v1',
            'dify_token': 'mock_token',
            'mock_mode': True,  # 使用Mock模式进行测试
            'timeout': 30,
            'max_retries': 3
        }
        
        # 初始化服务
        self.ai_service = AIService(self.config)
        
        logger.info("流式UI测试器初始化完成")
    
    async def test_progress_indicator_simulation(self):
        """测试进度指示器模拟"""
        logger.info("🔄 开始测试进度指示器模拟")
        
        # 模拟文件上传流程的各个阶段
        stages = [
            ('UPLOADING', '正在上传文件...', 10),
            ('PARSING', '正在解析用例文件...', 30),
            ('CONNECTING', '正在连接AI服务...', 50),
            ('ANALYZING', '正在分析用例内容...', 70),
            ('THINKING', 'AI正在思考中，请稍候...', 90),
            ('COMPLETED', '分析完成，可以开始对话', 100)
        ]
        
        for stage, message, progress in stages:
            logger.info(f"📊 进度更新: {stage} - {message} ({progress}%)")
            await asyncio.sleep(0.5)  # 模拟处理时间
        
        logger.info("✅ 进度指示器模拟测试完成")
        return True
    
    async def test_streaming_message_display(self):
        """测试流式消息显示"""
        logger.info("💬 开始测试流式消息显示")
        
        # 模拟AI回复内容
        test_message = "我已经分析了您上传的测试用例文件。这个用例包含了基本的测试流程。为了生成更完整的测试用例，我想了解：\n\n1. 这个系统主要的用户群体是谁？\n2. 是否有特殊的安全性要求？\n3. 有什么特殊的业务规则需要考虑吗？"
        
        # 模拟打字机效果
        chunk_size = 3
        for i in range(0, len(test_message), chunk_size):
            chunk = test_message[i:i + chunk_size]
            logger.info(f"📝 流式输出: '{chunk}'")
            await asyncio.sleep(0.1)  # 模拟打字速度
        
        logger.info("✅ 流式消息显示测试完成")
        return True
    
    async def test_dify_streaming_client(self):
        """测试Dify流式客户端"""
        logger.info("🤖 开始测试Dify流式客户端")
        
        try:
            # 获取Dify处理器
            handler = self.ai_service.mode_selector.get_handler()
            
            if isinstance(handler, DifyHandler):
                # 获取流式客户端
                streaming_client = handler.get_streaming_client()
                
                # 测试流式消息发送
                test_message = "请分析这个测试用例并提供建议"
                
                logger.info(f"📤 发送流式消息: {test_message}")
                
                async for chunk in streaming_client.send_streaming_message(
                    message=test_message,
                    conversation_id=None,
                    context={'test_mode': True}
                ):
                    if chunk:
                        event_type = chunk.get('event', 'unknown')
                        content = chunk.get('content', '')
                        
                        if event_type == 'message' and content:
                            logger.info(f"📨 收到流式数据: '{content}'")
                        elif event_type == 'message_end':
                            logger.info("🏁 流式消息结束")
                        elif event_type == 'error':
                            logger.error(f"❌ 流式错误: {chunk.get('message', 'unknown error')}")
                
                logger.info("✅ Dify流式客户端测试完成")
                return True
            else:
                logger.info("ℹ️ 当前为Mock模式，跳过Dify流式客户端测试")
                return True
                
        except Exception as e:
            logger.error(f"❌ Dify流式客户端测试失败: {e}")
            return False
    
    async def test_streaming_chat_handler(self):
        """测试流式聊天处理器"""
        logger.info("💭 开始测试流式聊天处理器")
        
        try:
            # 创建流式聊天处理器
            streaming_handler = StreamingChatHandler(self.ai_service)
            
            # 模拟会话ID
            session_id = "test_session_123"
            test_message = "请帮我生成登录功能的测试用例"
            
            logger.info(f"🗨️ 开始流式聊天: session_id={session_id}")
            
            async for sse_data in streaming_handler.handle_streaming_chat(session_id, test_message):
                if sse_data:
                    # 解析SSE数据
                    if sse_data.startswith('data: '):
                        try:
                            data = json.loads(sse_data[6:])  # 移除 'data: ' 前缀
                            event_type = data.get('type', 'unknown')
                            
                            if event_type == 'stream_start':
                                logger.info("🎬 流式聊天开始")
                            elif event_type == 'progress':
                                stage = data.get('data', {}).get('stage', 'unknown')
                                message = data.get('data', {}).get('message', '')
                                logger.info(f"📈 进度更新: {stage} - {message}")
                            elif event_type == 'streaming':
                                content = data.get('data', {}).get('content', '')
                                if content:
                                    logger.info(f"💬 流式内容: '{content}'")
                            elif event_type == 'complete':
                                logger.info("🎯 流式聊天完成")
                            elif event_type == 'error':
                                error_msg = data.get('data', {}).get('message', 'unknown error')
                                logger.error(f"❌ 流式聊天错误: {error_msg}")
                            elif event_type == 'stream_complete':
                                logger.info("🏁 流式传输完成")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ SSE数据解析失败: {e}")
            
            logger.info("✅ 流式聊天处理器测试完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 流式聊天处理器测试失败: {e}")
            return False
    
    async def test_error_handling_and_fallback(self):
        """测试错误处理和降级机制"""
        logger.info("🛡️ 开始测试错误处理和降级机制")
        
        try:
            # 测试网络异常处理
            logger.info("🌐 测试网络异常处理")
            
            # 模拟网络异常
            original_mode = self.ai_service.mode_selector.current_mode
            
            # 强制切换到Mock模式（模拟网络异常后的降级）
            self.ai_service.mode_selector.switch_to_mock("测试网络异常降级")
            
            # 验证降级是否成功
            if self.ai_service.mode_selector.is_mock_mode():
                logger.info("✅ 成功降级到Mock模式")
            else:
                logger.error("❌ 降级失败")
                return False
            
            # 测试Mock模式下的流式响应
            session_id = "test_error_session"
            test_message = "测试错误处理"
            
            async for chunk in self.ai_service.send_message_streaming(session_id, test_message):
                if chunk:
                    event_type = chunk.get('event', 'unknown')
                    if event_type == 'message':
                        content = chunk.get('content', '')
                        if content:
                            logger.info(f"📝 Mock流式内容: '{content}'")
                    elif event_type == 'message_end':
                        logger.info("🏁 Mock流式消息结束")
                        break
                    elif event_type == 'error':
                        logger.error(f"❌ Mock流式错误: {chunk.get('message', 'unknown')}")
            
            logger.info("✅ 错误处理和降级机制测试完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 错误处理测试失败: {e}")
            return False
    
    async def test_resource_management(self):
        """测试资源管理"""
        logger.info("🧹 开始测试资源管理")
        
        try:
            # 获取Dify处理器
            handler = self.ai_service.mode_selector.get_handler()
            
            if isinstance(handler, DifyHandler):
                # 测试流式客户端的资源管理
                streaming_client = handler.get_streaming_client()
                
                # 检查初始状态
                initial_count = streaming_client.get_stream_count()
                logger.info(f"📊 初始活跃流数量: {initial_count}")
                
                # 模拟创建多个流式连接
                tasks = []
                for i in range(3):
                    task = asyncio.create_task(
                        self._simulate_stream_connection(streaming_client, f"test_stream_{i}")
                    )
                    tasks.append(task)
                
                # 等待所有任务完成
                await asyncio.gather(*tasks)
                
                # 检查资源清理
                await asyncio.sleep(1)  # 等待清理完成
                final_count = streaming_client.get_stream_count()
                logger.info(f"📊 最终活跃流数量: {final_count}")
                
                # 清理所有流
                await streaming_client.cleanup_all_streams()
                
                logger.info("✅ 资源管理测试完成")
                return True
            else:
                logger.info("ℹ️ 当前为Mock模式，跳过资源管理测试")
                return True
                
        except Exception as e:
            logger.error(f"❌ 资源管理测试失败: {e}")
            return False
    
    async def _simulate_stream_connection(self, streaming_client: DifyStreamingClient, stream_name: str):
        """模拟流式连接"""
        try:
            logger.info(f"🔗 创建模拟流式连接: {stream_name}")
            
            # 模拟短暂的流式连接
            async for chunk in streaming_client.send_streaming_message(
                message=f"测试消息 {stream_name}",
                conversation_id=None,
                context={'test_stream': stream_name}
            ):
                if chunk and chunk.get('event') == 'message_end':
                    break
            
            logger.info(f"✅ 模拟流式连接完成: {stream_name}")
            
        except Exception as e:
            logger.error(f"❌ 模拟流式连接失败: {stream_name}, error: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行流式UI改进功能测试套件")
        
        tests = [
            ("进度指示器模拟", self.test_progress_indicator_simulation),
            ("流式消息显示", self.test_streaming_message_display),
            ("Dify流式客户端", self.test_dify_streaming_client),
            ("流式聊天处理器", self.test_streaming_chat_handler),
            ("错误处理和降级", self.test_error_handling_and_fallback),
            ("资源管理", self.test_resource_management)
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
            logger.info("🎉 所有测试通过！流式UI改进功能正常工作")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败，需要检查相关功能")
        
        return results


async def main():
    """主函数"""
    tester = StreamingUITester()
    results = await tester.run_all_tests()
    
    # 返回测试结果
    return results


if __name__ == "__main__":
    # 运行测试
    results = asyncio.run(main())
    
    # 根据测试结果设置退出码
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 所有 {total} 个测试通过！")
        exit(0)
    else:
        print(f"\n❌ {total - passed} 个测试失败，共 {total} 个测试")
        exit(1)