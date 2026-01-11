"""
流式聊天处理器 - 处理Server-Sent Events (SSE)格式的流式聊天响应

这个模块实现了StreamingChatHandler类，用于处理Dify的流式API调用
并将响应转换为前端可以处理的SSE格式。
"""

import json
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime
from services.ai_service import AIService, DifyAPIError, NetworkError, ConversationNotFoundError

logger = logging.getLogger(__name__)


class StreamingChatHandler:
    """
    流式聊天处理器
    
    负责处理流式聊天请求，调用Dify流式API，并将响应转换为
    Server-Sent Events (SSE) 格式供前端消费。
    """
    
    def __init__(self, ai_service: AIService):
        """
        初始化流式聊天处理器
        
        Args:
            ai_service: AI服务实例
        """
        self.ai_service = ai_service
        self.active_streams = {}  # 活跃的流式连接
        
        logger.info("StreamingChatHandler初始化完成")
    
    async def handle_streaming_chat(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """
        处理流式聊天请求
        
        Args:
            session_id: 会话ID
            message: 用户消息
            
        Yields:
            str: SSE格式的响应数据
        """
        stream_id = f"stream_{session_id}_{datetime.now().timestamp()}"
        
        try:
            # 记录活跃流
            self.active_streams[stream_id] = {
                'session_id': session_id,
                'started_at': datetime.now(),
                'status': 'active'
            }
            
            logger.info(f"开始处理流式聊天: session_id={session_id}, stream_id={stream_id}")
            
            # 发送开始事件
            yield self._format_sse_data({
                'type': 'stream_start',
                'data': {
                    'session_id': session_id,
                    'stream_id': stream_id,
                    'message': '开始处理您的请求...'
                }
            })
            
            # 发送进度更新 - 连接AI服务
            yield self._format_sse_data({
                'type': 'progress',
                'data': {
                    'stage': 'connecting',
                    'message': '正在连接AI服务...',
                    'progress': 10
                }
            })
            
            # 调用AI服务获取流式响应
            try:
                async for chunk in self._process_ai_stream(session_id, message):
                    if chunk:
                        yield self._format_sse_data(chunk)
                        
            except ConversationNotFoundError as e:
                logger.error(f"对话不存在: {e}")
                yield self._format_sse_data({
                    'type': 'error',
                    'data': {
                        'error': 'conversation_not_found',
                        'message': '对话不存在或已过期，请刷新页面重新开始',
                        'user_message': '对话已过期，请刷新页面重新开始'
                    }
                })
                return
                
            except NetworkError as e:
                logger.error(f"网络连接异常: {e}")
                yield self._format_sse_data({
                    'type': 'error',
                    'data': {
                        'error': 'network_error',
                        'message': str(e),
                        'user_message': '网络连接异常，请检查网络后重试'
                    }
                })
                return
                
            except DifyAPIError as e:
                logger.error(f"Dify API异常: {e}")
                yield self._format_sse_data({
                    'type': 'error',
                    'data': {
                        'error': 'api_error',
                        'message': str(e),
                        'user_message': 'AI服务暂时不可用，请稍后重试'
                    }
                })
                return
            
            # 发送完成事件
            yield self._format_sse_data({
                'type': 'stream_complete',
                'data': {
                    'session_id': session_id,
                    'stream_id': stream_id,
                    'message': '响应完成'
                }
            })
            
            logger.info(f"流式聊天处理完成: session_id={session_id}, stream_id={stream_id}")
            
        except Exception as e:
            logger.error(f"流式聊天处理异常: session_id={session_id}, error={e}")
            
            # 发送错误事件
            yield self._format_sse_data({
                'type': 'error',
                'data': {
                    'error': 'internal_error',
                    'message': str(e),
                    'user_message': '服务器内部错误，请稍后重试'
                }
            })
            
        finally:
            # 清理活跃流记录
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'completed'
                self.active_streams[stream_id]['completed_at'] = datetime.now()
                
                # 延迟清理（保留一段时间用于调试）
                asyncio.create_task(self._cleanup_stream(stream_id, delay=300))  # 5分钟后清理
    
    async def _process_ai_stream(self, session_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理AI服务的流式响应
        
        Args:
            session_id: 会话ID
            message: 用户消息
            
        Yields:
            Dict[str, Any]: 处理后的流式数据
        """
        try:
            # 发送进度更新 - 开始分析
            yield {
                'type': 'progress',
                'data': {
                    'stage': 'analyzing',
                    'message': '正在分析您的消息...',
                    'progress': 30
                }
            }
            
            # 调用AI服务的流式方法
            stream_generator = self.ai_service.send_message_streaming(session_id, message)
            
            # 发送进度更新 - 开始接收响应
            yield {
                'type': 'progress',
                'data': {
                    'stage': 'streaming',
                    'message': 'AI正在思考中...',
                    'progress': 50
                }
            }
            
            message_content = ""
            async for chunk in stream_generator:
                if chunk and isinstance(chunk, dict):
                    event_type = chunk.get('event', '')
                    
                    if event_type == 'message':
                        # 处理消息块
                        content = chunk.get('content', '')
                        if content:
                            message_content += content
                            yield {
                                'type': 'streaming',
                                'data': {
                                    'content': content,
                                    'finished': False,
                                    'message_id': chunk.get('message_id'),
                                    'conversation_id': chunk.get('conversation_id')
                                }
                            }
                    
                    elif event_type == 'message_end':
                        # 处理消息结束
                        yield {
                            'type': 'complete',
                            'data': {
                                'content': message_content,
                                'message_id': chunk.get('message_id'),
                                'conversation_id': chunk.get('conversation_id'),
                                'metadata': chunk.get('metadata', {}),
                                'usage': chunk.get('usage', {})
                            }
                        }
                    
                    elif event_type == 'workflow_started':
                        # 处理工作流开始
                        yield {
                            'type': 'progress',
                            'data': {
                                'stage': 'workflow_started',
                                'message': '工作流开始执行...',
                                'progress': chunk.get('progress', 60),
                                'workflow_run_id': chunk.get('workflow_run_id')
                            }
                        }
                    
                    elif event_type == 'node_started':
                        # 处理节点开始
                        node_type = chunk.get('node_type', 'unknown')
                        yield {
                            'type': 'progress',
                            'data': {
                                'stage': f'node_{node_type}_running',
                                'message': f'正在执行 {node_type} 节点...',
                                'progress': chunk.get('progress', 70),
                                'node_id': chunk.get('node_id'),
                                'node_type': node_type
                            }
                        }
                    
                    elif event_type == 'node_finished':
                        # 处理节点完成
                        node_type = chunk.get('node_type', 'unknown')
                        status = chunk.get('status', 'succeeded')
                        yield {
                            'type': 'progress',
                            'data': {
                                'stage': f'node_{node_type}_finished',
                                'message': f'{node_type} 节点执行{"完成" if status == "succeeded" else "失败"}',
                                'progress': chunk.get('progress', 80),
                                'node_id': chunk.get('node_id'),
                                'node_type': node_type,
                                'status': status
                            }
                        }
                    
                    elif event_type == 'workflow_finished':
                        # 处理工作流完成
                        status = chunk.get('status', 'succeeded')
                        yield {
                            'type': 'progress',
                            'data': {
                                'stage': 'workflow_finished',
                                'message': f'工作流执行{"完成" if status == "succeeded" else "失败"}',
                                'progress': 90 if status == 'succeeded' else 0,
                                'status': status,
                                'outputs': chunk.get('outputs', {})
                            }
                        }
                    
                    elif event_type == 'error':
                        # 处理错误事件
                        yield {
                            'type': 'error',
                            'data': {
                                'error': chunk.get('code', 'unknown_error'),
                                'message': chunk.get('message', '发生未知错误'),
                                'user_message': chunk.get('user_message', '处理过程中发生错误')
                            }
                        }
                        return
                        
        except Exception as e:
            logger.error(f"处理AI流式响应异常: session_id={session_id}, error={e}")
            yield {
                'type': 'error',
                'data': {
                    'error': 'stream_processing_error',
                    'message': str(e),
                    'user_message': '处理AI响应时发生错误'
                }
            }
    
    def _format_sse_data(self, data: Dict[str, Any]) -> str:
        """
        格式化为SSE数据格式
        
        Args:
            data: 要发送的数据
            
        Returns:
            str: SSE格式的数据
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            return f"data: {json_data}\n\n"
        except Exception as e:
            logger.error(f"格式化SSE数据失败: {e}")
            error_data = {
                'type': 'error',
                'data': {
                    'error': 'format_error',
                    'message': '数据格式化失败'
                }
            }
            return f"data: {json.dumps(error_data)}\n\n"
    
    async def _cleanup_stream(self, stream_id: str, delay: int = 300):
        """
        清理流式连接记录
        
        Args:
            stream_id: 流ID
            delay: 延迟时间（秒）
        """
        try:
            await asyncio.sleep(delay)
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                logger.debug(f"清理流式连接记录: stream_id={stream_id}")
        except Exception as e:
            logger.error(f"清理流式连接记录失败: stream_id={stream_id}, error={e}")
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """
        获取活跃的流式连接信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 活跃流信息
        """
        return self.active_streams.copy()
    
    def get_stream_count(self) -> int:
        """
        获取活跃流的数量
        
        Returns:
            int: 活跃流数量
        """
        return len([s for s in self.active_streams.values() if s['status'] == 'active'])
    
    async def cleanup_all_streams(self):
        """清理所有流式连接记录"""
        try:
            stream_count = len(self.active_streams)
            self.active_streams.clear()
            logger.info(f"清理所有流式连接记录: {stream_count} 个")
        except Exception as e:
            logger.error(f"清理所有流式连接记录失败: {e}")