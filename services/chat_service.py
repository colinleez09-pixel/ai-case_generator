import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.ai_service import AIService
from services.session_service import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务 - 管理AI对话交互和上下文"""
    
    def __init__(self, ai_service: AIService, session_service: SessionService):
        """
        初始化对话服务
        
        Args:
            ai_service: AI服务实例
            session_service: 会话服务实例
        """
        self.ai_service = ai_service
        self.session_service = session_service
        
        # 关键词配置
        self.generation_keywords = [
            '开始生成', 'start generation', 'generate', '生成用例',
            'begin', 'start', '开始', '生成测试用例'
        ]
        
        logger.info("对话服务初始化完成")
    
    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        发送消息并获取AI回复
        
        Args:
            session_id: 会话ID
            message: 用户消息
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            # 获取会话数据
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            # 检查会话状态
            current_status = session_data.get('status', 'unknown')
            if current_status not in ['analyzing', 'chatting']:
                return {
                    'success': False,
                    'error': 'invalid_status',
                    'message': f'当前会话状态不支持对话: {current_status}'
                }
            
            # 添加用户消息到对话历史
            self._add_message_to_history(session_id, 'user', message)
            
            # 检查是否触发生成关键词
            ready_to_generate = self._check_generation_keywords(message)
            
            if ready_to_generate:
                # 更新会话状态为准备生成
                self.session_service.update_session_data(session_id, {
                    'status': 'ready_to_generate',
                    'updated_at': datetime.utcnow().isoformat()
                })
                
                # 添加AI确认消息
                ai_reply = "好的，我现在开始为您生成测试用例。请稍等..."
                self._add_message_to_history(session_id, 'ai', ai_reply)
                
                return {
                    'success': True,
                    'reply': ai_reply,
                    'need_more_info': False,
                    'ready_to_generate': True,
                    'session_status': 'ready_to_generate'
                }
            
            # 获取对话上下文
            context = self._build_chat_context(session_data)
            
            # 获取Dify对话ID（用于多轮对话）
            dify_conversation_id = self.session_service.get_dify_conversation_id(session_id)
            context['dify_conversation_id'] = dify_conversation_id
            
            # 获取Dify系统参数（用于多轮对话）
            dify_system_params = self.session_service.get_dify_system_params(session_id)
            context['dify_system_params'] = dify_system_params
            
            logger.info(f"当前Dify对话ID: session_id={session_id}, dify_conversation_id={dify_conversation_id}")
            logger.debug(f"当前Dify系统参数: {dify_system_params}")
            
            # 调用AI服务获取回复 - 使用异步调用
            import asyncio
            
            async def call_ai_service():
                return await self.ai_service.chat_with_agent(session_id, message, context)
            
            try:
                # 检查是否已经在事件循环中
                try:
                    loop = asyncio.get_running_loop()
                    # 如果已经在事件循环中，需要使用不同的方法
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, call_ai_service())
                        ai_response = future.result()
                except RuntimeError:
                    # 如果没有运行的事件循环，直接运行
                    ai_response = asyncio.run(call_ai_service())
            except Exception as loop_error:
                logger.error(f"事件循环处理失败: {loop_error}")
                # 降级到Mock处理
                ai_response = {'reply': '抱歉，服务暂时不可用，请稍后重试。', 'need_more_info': True}
            
            # 检查是否是conversation过期的情况
            if ai_response.get('conversation_expired'):
                expired_conversation_id = ai_response.get('expired_conversation_id')
                logger.warning(f"Conversation过期，清除并重试: {expired_conversation_id}")
                
                # 清除过期的conversation_id
                self.session_service.clear_dify_conversation_id(session_id)
                
                # 重新调用AI服务（这次不会有conversation_id）
                context['dify_conversation_id'] = None
                try:
                    ai_response = asyncio.run(call_ai_service())
                except Exception as retry_error:
                    logger.error(f"重试调用失败: {retry_error}")
                    ai_response = {'reply': '抱歉，服务暂时不可用，请稍后重试。', 'need_more_info': True}
                
                logger.info(f"重新开始对话成功，新的conversation_id: {ai_response.get('conversation_id')}")
            
            # 如果获得了新的conversation_id，保存到SessionService
            new_conversation_id = ai_response.get('conversation_id')
            if new_conversation_id and new_conversation_id != dify_conversation_id:
                self.session_service.update_dify_conversation_id(session_id, new_conversation_id)
                logger.info(f"保存新的Dify对话ID: session_id={session_id}, conversation_id={new_conversation_id}")
            
            # 如果获得了系统参数，保存到SessionService
            dify_system_params = ai_response.get('dify_system_params')
            if dify_system_params:
                self.session_service.update_dify_system_params(session_id, dify_system_params)
                logger.info(f"保存Dify系统参数: session_id={session_id}, params={dify_system_params}")
            
            # 添加AI回复到对话历史
            ai_reply = ai_response.get('reply', '抱歉，我无法理解您的问题。')
            self._add_message_to_history(session_id, 'ai', ai_reply)
            
            # 更新会话状态
            if current_status == 'analyzing':
                self.session_service.update_session_data(session_id, {
                    'status': 'chatting',
                    'updated_at': datetime.utcnow().isoformat()
                })
            
            # 延长会话有效期
            self.session_service.extend_session(session_id)
            
            return {
                'success': True,
                'reply': ai_reply,
                'need_more_info': ai_response.get('need_more_info', True),
                'ready_to_generate': ai_response.get('ready_to_generate', False),
                'suggestions': ai_response.get('suggestions', []),
                'session_status': 'chatting'
            }
            
        except Exception as e:
            logger.error(f"发送消息失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'chat_error',
                'message': '对话处理失败，请重试'
            }
    
    def get_chat_history(self, session_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            limit: 限制返回的消息数量
            
        Returns:
            Dict[str, Any]: 对话历史
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            # 获取会话数据
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            chat_history = session_data.get('chat_history', [])
            
            # 应用限制
            if limit and limit > 0:
                chat_history = chat_history[-limit:]
            
            return {
                'success': True,
                'chat_history': chat_history,
                'total_messages': len(session_data.get('chat_history', []))
            }
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'get_history_error',
                'message': '获取对话历史失败'
            }
    
    def clear_chat_history(self, session_id: str) -> Dict[str, Any]:
        """
        清空对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            # 清空对话历史
            self.session_service.update_session_data(session_id, {
                'chat_history': [],
                'updated_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"清空对话历史成功: {session_id}")
            return {
                'success': True,
                'message': '对话历史已清空'
            }
            
        except Exception as e:
            logger.error(f"清空对话历史失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'clear_history_error',
                'message': '清空对话历史失败'
            }
    
    def _add_message_to_history(self, session_id: str, role: str, message: str) -> None:
        """
        添加消息到对话历史
        
        Args:
            session_id: 会话ID
            role: 角色 (user|ai)
            message: 消息内容
        """
        try:
            # 使用会话服务的添加消息方法
            self.session_service.add_chat_message(session_id, role, message)
            
        except Exception as e:
            logger.error(f"添加消息到历史失败: {session_id}, {e}")
    
    def _check_generation_keywords(self, message: str) -> bool:
        """
        检查消息是否包含生成关键词
        
        Args:
            message: 用户消息
            
        Returns:
            bool: 是否包含生成关键词
        """
        message_lower = message.lower().strip()
        
        for keyword in self.generation_keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    def _build_chat_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建对话上下文
        
        Args:
            session_data: 会话数据
            
        Returns:
            Dict[str, Any]: 对话上下文
        """
        context = {
            'session_id': session_data.get('session_id'),
            'status': session_data.get('status'),
            'chat_history': session_data.get('chat_history', []),
            'files_info': session_data.get('files', {}),
            'config': session_data.get('config', {}),
            'analysis_result': session_data.get('analysis_result', {})
        }
        
        # 添加统计信息
        context['stats'] = {
            'total_messages': len(context['chat_history']),
            'user_messages': len([msg for msg in context['chat_history'] if msg.get('role') == 'user']),
            'ai_messages': len([msg for msg in context['chat_history'] if msg.get('role') == 'ai']),
            'files_count': len(context['files_info'])
        }
        
        return context
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话状态
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            # 获取会话数据
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            # 构建状态信息
            status_info = {
                'session_id': session_id,
                'status': session_data.get('status', 'unknown'),
                'created_at': session_data.get('created_at'),
                'updated_at': session_data.get('updated_at'),
                'message_count': len(session_data.get('chat_history', [])),
                'files_uploaded': len(session_data.get('files', {})),
                'ready_to_generate': session_data.get('status') == 'ready_to_generate'
            }
            
            return {
                'success': True,
                'status_info': status_info
            }
            
        except Exception as e:
            logger.error(f"获取会话状态失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'get_status_error',
                'message': '获取会话状态失败'
            }
    
    def reset_session_status(self, session_id: str, new_status: str = 'chatting') -> Dict[str, Any]:
        """
        重置会话状态
        
        Args:
            session_id: 会话ID
            new_status: 新状态
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            # 更新会话状态
            self.session_service.update_session_data(session_id, {
                'status': new_status,
                'updated_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"重置会话状态成功: {session_id} -> {new_status}")
            return {
                'success': True,
                'message': f'会话状态已重置为: {new_status}'
            }
            
        except Exception as e:
            logger.error(f"重置会话状态失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'reset_status_error',
                'message': '重置会话状态失败'
            }