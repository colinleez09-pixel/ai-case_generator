import json
import time
import random
import logging
import asyncio
import aiohttp
import uuid
from typing import Dict, Any, List, Generator, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


# 自定义异常类
class DifyAPIError(Exception):
    """Dify API异常"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ConversationNotFoundError(DifyAPIError):
    """对话不存在异常"""
    pass


class NetworkError(Exception):
    """网络连接异常"""
    pass


class ProgressTracker:
    """进度跟踪器 - 跟踪工作流和节点执行进度"""
    
    def __init__(self):
        """初始化进度跟踪器"""
        self.workflows = {}  # workflow_run_id -> workflow_info
        self.progress_callbacks = []  # 进度更新回调函数列表
        
        logger.info("ProgressTracker初始化完成")
    
    def add_progress_callback(self, callback):
        """
        添加进度更新回调函数
        
        Args:
            callback: 回调函数，接收(workflow_run_id, progress_info)参数
        """
        self.progress_callbacks.append(callback)
    
    def start_workflow(self, workflow_run_id: str, workflow_data: Dict[str, Any]):
        """
        开始工作流跟踪
        
        Args:
            workflow_run_id: 工作流运行ID
            workflow_data: 工作流数据
        """
        self.workflows[workflow_run_id] = {
            'workflow_id': workflow_data.get('workflow_id'),
            'status': 'running',
            'progress': 0,
            'nodes': {},
            'started_at': datetime.utcnow(),
            'current_stage': 'workflow_started',
            'total_nodes': 0,
            'completed_nodes': 0,
            'metadata': workflow_data
        }
        
        self._notify_progress(workflow_run_id)
        logger.info(f"开始跟踪工作流: {workflow_run_id}")
    
    def start_node(self, workflow_run_id: str, node_data: Dict[str, Any]):
        """
        开始节点跟踪
        
        Args:
            workflow_run_id: 工作流运行ID
            node_data: 节点数据
        """
        if workflow_run_id not in self.workflows:
            logger.warning(f"未找到工作流: {workflow_run_id}")
            return
        
        node_id = node_data.get('node_id')
        node_type = node_data.get('node_type')
        
        workflow = self.workflows[workflow_run_id]
        workflow['nodes'][node_id] = {
            'node_id': node_id,
            'node_type': node_type,
            'status': 'running',
            'started_at': datetime.utcnow(),
            'metadata': node_data
        }
        
        # 更新总节点数
        workflow['total_nodes'] = len(workflow['nodes'])
        workflow['current_stage'] = f"node_{node_type}_running"
        
        # 计算进度 (已完成节点数 / 总节点数 * 80% + 10%)
        # 10%为工作流开始，80%为节点执行，10%为工作流完成
        if workflow['total_nodes'] > 0:
            node_progress = (workflow['completed_nodes'] / workflow['total_nodes']) * 80
            workflow['progress'] = min(10 + node_progress, 90)
        
        self._notify_progress(workflow_run_id)
        logger.debug(f"开始跟踪节点: {workflow_run_id}/{node_id} ({node_type})")
    
    def finish_node(self, workflow_run_id: str, node_data: Dict[str, Any]):
        """
        完成节点跟踪
        
        Args:
            workflow_run_id: 工作流运行ID
            node_data: 节点数据
        """
        if workflow_run_id not in self.workflows:
            logger.warning(f"未找到工作流: {workflow_run_id}")
            return
        
        node_id = node_data.get('node_id')
        status = node_data.get('status', 'succeeded')
        
        workflow = self.workflows[workflow_run_id]
        
        if node_id in workflow['nodes']:
            workflow['nodes'][node_id].update({
                'status': status,
                'finished_at': datetime.utcnow(),
                'outputs': node_data.get('outputs', {}),
                'error': node_data.get('error') if status != 'succeeded' else None,
                'execution_metadata': node_data.get('execution_metadata', {})
            })
            
            # 更新已完成节点数
            if status == 'succeeded':
                workflow['completed_nodes'] += 1
            
            # 重新计算进度
            if workflow['total_nodes'] > 0:
                node_progress = (workflow['completed_nodes'] / workflow['total_nodes']) * 80
                workflow['progress'] = min(10 + node_progress, 90)
            
            workflow['current_stage'] = f"node_{node_data.get('node_type', 'unknown')}_{status}"
            
            self._notify_progress(workflow_run_id)
            logger.debug(f"完成节点跟踪: {workflow_run_id}/{node_id} ({status})")
    
    def finish_workflow(self, workflow_run_id: str, workflow_data: Dict[str, Any]):
        """
        完成工作流跟踪
        
        Args:
            workflow_run_id: 工作流运行ID
            workflow_data: 工作流数据
        """
        if workflow_run_id not in self.workflows:
            logger.warning(f"未找到工作流: {workflow_run_id}")
            return
        
        status = workflow_data.get('status', 'succeeded')
        
        workflow = self.workflows[workflow_run_id]
        workflow.update({
            'status': status,
            'finished_at': datetime.utcnow(),
            'progress': 100 if status == 'succeeded' else workflow['progress'],
            'current_stage': 'workflow_finished',
            'outputs': workflow_data.get('outputs', {}),
            'error': workflow_data.get('error') if status != 'succeeded' else None
        })
        
        self._notify_progress(workflow_run_id)
        logger.info(f"完成工作流跟踪: {workflow_run_id} ({status})")
    
    def get_workflow_progress(self, workflow_run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流进度信息
        
        Args:
            workflow_run_id: 工作流运行ID
            
        Returns:
            Optional[Dict[str, Any]]: 进度信息
        """
        if workflow_run_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_run_id]
        
        # 计算执行时间
        started_at = workflow['started_at']
        finished_at = workflow.get('finished_at')
        
        if finished_at:
            duration = (finished_at - started_at).total_seconds()
        else:
            duration = (datetime.utcnow() - started_at).total_seconds()
        
        return {
            'workflow_run_id': workflow_run_id,
            'workflow_id': workflow['workflow_id'],
            'status': workflow['status'],
            'progress': workflow['progress'],
            'current_stage': workflow['current_stage'],
            'total_nodes': workflow['total_nodes'],
            'completed_nodes': workflow['completed_nodes'],
            'duration': duration,
            'started_at': started_at.isoformat(),
            'finished_at': finished_at.isoformat() if finished_at else None,
            'nodes': workflow['nodes'],
            'outputs': workflow.get('outputs', {}),
            'error': workflow.get('error')
        }
    
    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有工作流的进度信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有工作流的进度信息
        """
        result = {}
        for workflow_run_id in self.workflows:
            result[workflow_run_id] = self.get_workflow_progress(workflow_run_id)
        return result
    
    def cleanup_finished_workflows(self, max_age_hours: int = 24):
        """
        清理已完成的工作流记录
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        current_time = datetime.utcnow()
        workflows_to_remove = []
        
        for workflow_run_id, workflow in self.workflows.items():
            if workflow['status'] in ['succeeded', 'failed']:
                finished_at = workflow.get('finished_at', workflow['started_at'])
                age_hours = (current_time - finished_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    workflows_to_remove.append(workflow_run_id)
        
        for workflow_run_id in workflows_to_remove:
            del self.workflows[workflow_run_id]
            logger.info(f"清理已完成的工作流记录: {workflow_run_id}")
    
    def _notify_progress(self, workflow_run_id: str):
        """
        通知进度更新
        
        Args:
            workflow_run_id: 工作流运行ID
        """
        progress_info = self.get_workflow_progress(workflow_run_id)
        
        for callback in self.progress_callbacks:
            try:
                callback(workflow_run_id, progress_info)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")


class EventProcessor:
    """事件处理器 - 处理各种Dify事件并触发相应的业务逻辑"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        """
        初始化事件处理器
        
        Args:
            progress_tracker: 进度跟踪器
        """
        self.progress_tracker = progress_tracker
        self.event_handlers = {
            'message': self._handle_message_event,
            'message_end': self._handle_message_end_event,
            'workflow_started': self._handle_workflow_started_event,
            'workflow_finished': self._handle_workflow_finished_event,
            'node_started': self._handle_node_started_event,
            'node_finished': self._handle_node_finished_event,
            'error': self._handle_error_event
        }
        self.message_completion_callbacks = []  # 消息完成回调
        self.error_callbacks = []  # 错误回调
        
        logger.info("EventProcessor初始化完成")
    
    def add_message_completion_callback(self, callback):
        """
        添加消息完成回调
        
        Args:
            callback: 回调函数，接收(message_data)参数
        """
        self.message_completion_callbacks.append(callback)
    
    def add_error_callback(self, callback):
        """
        添加错误回调
        
        Args:
            callback: 回调函数，接收(error_data)参数
        """
        self.error_callbacks.append(callback)
    
    async def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        event_type = event_data.get('event')
        
        if event_type in self.event_handlers:
            try:
                result = await self.event_handlers[event_type](event_data)
                logger.debug(f"事件处理完成: {event_type}")
                return result
            except Exception as e:
                logger.error(f"事件处理失败: {event_type}, error: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'event_type': event_type
                }
        else:
            logger.warning(f"未知事件类型: {event_type}")
            return {
                'success': False,
                'error': f'Unknown event type: {event_type}',
                'event_type': event_type
            }
    
    async def _handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息事件"""
        # 消息事件通常不需要特殊处理，只是传递内容
        return {
            'success': True,
            'action': 'message_received',
            'content': event_data.get('content', ''),
            'message_id': event_data.get('message_id')
        }
    
    async def _handle_message_end_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息结束事件"""
        # 标记对话完成
        message_id = event_data.get('message_id')
        conversation_id = event_data.get('conversation_id')
        
        # 触发消息完成回调
        for callback in self.message_completion_callbacks:
            try:
                await callback(event_data)
            except Exception as e:
                logger.error(f"消息完成回调执行失败: {e}")
        
        logger.info(f"对话完成: message_id={message_id}, conversation_id={conversation_id}")
        
        return {
            'success': True,
            'action': 'conversation_completed',
            'message_id': message_id,
            'conversation_id': conversation_id,
            'metadata': event_data.get('metadata', {})
        }
    
    async def _handle_workflow_started_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理工作流开始事件"""
        workflow_run_id = event_data.get('workflow_run_id')
        workflow_data = event_data.get('metadata', {}).get('workflow_data', {})
        
        # 开始进度跟踪
        self.progress_tracker.start_workflow(workflow_run_id, workflow_data)
        
        return {
            'success': True,
            'action': 'workflow_started',
            'workflow_run_id': workflow_run_id,
            'progress': 10
        }
    
    async def _handle_workflow_finished_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理工作流完成事件"""
        workflow_run_id = event_data.get('workflow_run_id')
        status = event_data.get('status', 'succeeded')
        workflow_data = event_data.get('metadata', {}).get('workflow_data', {})
        
        # 完成进度跟踪
        self.progress_tracker.finish_workflow(workflow_run_id, workflow_data)
        
        return {
            'success': True,
            'action': 'workflow_finished',
            'workflow_run_id': workflow_run_id,
            'status': status,
            'progress': 100 if status == 'succeeded' else 0,
            'outputs': event_data.get('outputs', {})
        }
    
    async def _handle_node_started_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点开始事件"""
        workflow_run_id = event_data.get('workflow_run_id')
        node_data = event_data.get('metadata', {}).get('node_data', {})
        
        # 开始节点跟踪
        self.progress_tracker.start_node(workflow_run_id, node_data)
        
        # 获取更新后的进度
        progress_info = self.progress_tracker.get_workflow_progress(workflow_run_id)
        current_progress = progress_info['progress'] if progress_info else 0
        
        return {
            'success': True,
            'action': 'node_started',
            'workflow_run_id': workflow_run_id,
            'node_id': event_data.get('node_id'),
            'node_type': event_data.get('node_type'),
            'progress': current_progress
        }
    
    async def _handle_node_finished_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点完成事件"""
        workflow_run_id = event_data.get('workflow_run_id')
        node_data = event_data.get('metadata', {}).get('node_data', {})
        
        # 完成节点跟踪
        self.progress_tracker.finish_node(workflow_run_id, node_data)
        
        # 获取更新后的进度
        progress_info = self.progress_tracker.get_workflow_progress(workflow_run_id)
        current_progress = progress_info['progress'] if progress_info else 0
        
        return {
            'success': True,
            'action': 'node_finished',
            'workflow_run_id': workflow_run_id,
            'node_id': event_data.get('node_id'),
            'node_type': event_data.get('node_type'),
            'status': event_data.get('status', 'succeeded'),
            'progress': current_progress,
            'outputs': event_data.get('outputs', {})
        }
    
    async def _handle_error_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误事件"""
        error_status = event_data.get('status', 500)
        error_code = event_data.get('code', 'unknown_error')
        error_message = event_data.get('message', '发生未知错误')
        user_message = event_data.get('user_message', error_message)
        
        # 触发错误回调
        for callback in self.error_callbacks:
            try:
                await callback(event_data)
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}")
        
        logger.error(f"处理错误事件: {error_code} - {error_message}")
        
        return {
            'success': False,
            'action': 'error_occurred',
            'status': error_status,
            'code': error_code,
            'message': error_message,
            'user_message': user_message
        }


class StreamProcessor:
    """流式响应处理器 - 处理Dify的SSE格式流式响应"""
    
    def __init__(self, progress_tracker: Optional[ProgressTracker] = None, event_processor: Optional[EventProcessor] = None):
        """
        初始化流式响应处理器
        
        Args:
            progress_tracker: 进度跟踪器（可选）
            event_processor: 事件处理器（可选）
        """
        self.progress_tracker = progress_tracker
        self.event_processor = event_processor
        
        self.event_handlers = {
            'message': self._handle_message,
            'message_end': self._handle_message_end,
            'workflow_started': self._handle_workflow_started,
            'workflow_finished': self._handle_workflow_finished,
            'node_started': self._handle_node_started,
            'node_finished': self._handle_node_finished,
            'error': self._handle_error,
            'tts_message': self._handle_tts_message,
            'tts_message_end': self._handle_tts_message_end,
            'message_replace': self._handle_message_replace
        }
        
        logger.info("StreamProcessor初始化完成")
    
    def set_progress_tracker(self, progress_tracker: ProgressTracker):
        """设置进度跟踪器"""
        self.progress_tracker = progress_tracker
    
    def set_event_processor(self, event_processor: EventProcessor):
        """设置事件处理器"""
        self.event_processor = event_processor
    
    async def process_stream(self, response: aiohttp.ClientResponse) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理SSE流式响应
        
        Args:
            response: aiohttp响应对象
            
        Yields:
            Dict[str, Any]: 解析后的事件数据
        """
        try:
            logger.debug("开始处理SSE流式响应")
            
            async for line in response.content:
                if line:
                    line_str = line.decode('utf-8').strip()
                    
                    # 处理SSE格式的数据行
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        
                        # 检查是否是结束标记
                        if data_str.strip() == '[DONE]':
                            logger.debug("SSE流式响应完成")
                            break
                        
                        try:
                            # 解析JSON数据
                            data = json.loads(data_str)
                            event_type = data.get('event', '')
                            
                            logger.debug(f"收到SSE事件: {event_type}")
                            
                            # 处理事件
                            if event_type in self.event_handlers:
                                result = await self.event_handlers[event_type](data)
                                if result:
                                    # 如果有事件处理器，也让它处理事件
                                    if self.event_processor:
                                        try:
                                            await self.event_processor.process_event(result)
                                        except Exception as e:
                                            logger.error(f"事件处理器处理失败: {e}")
                                    
                                    yield result
                            else:
                                logger.warning(f"未知的SSE事件类型: {event_type}")
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析SSE数据失败: {e}, data: {data_str}")
                            continue
                            
        except Exception as e:
            logger.error(f"处理SSE流式响应异常: {e}")
            yield {
                'event': 'error',
                'error': str(e),
                'message': '流式响应处理失败'
            }
    
    async def process_stream_text(self, stream_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理文本格式的SSE流式响应（用于测试）
        
        Args:
            stream_text: SSE格式的文本
            
        Yields:
            Dict[str, Any]: 解析后的事件数据
        """
        try:
            lines = stream_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('data: '):
                    data_str = line[6:]  # 移除 'data: ' 前缀
                    
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        event_type = data.get('event', '')
                        
                        if event_type in self.event_handlers:
                            result = await self.event_handlers[event_type](data)
                            if result:
                                yield result
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"处理文本SSE流异常: {e}")
            yield {
                'event': 'error',
                'error': str(e)
            }
    
    async def _handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的消息数据
        """
        return {
            'event': 'message',
            'type': 'message_chunk',
            'content': data.get('answer', ''),
            'message_id': data.get('message_id', ''),
            'conversation_id': data.get('conversation_id', ''),
            'created_at': data.get('created_at'),
            'metadata': {
                'task_id': data.get('task_id'),
                'raw_data': data
            }
        }
    
    async def _handle_message_end(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息结束事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的消息结束数据
        """
        return {
            'event': 'message_end',
            'type': 'message_complete',
            'message_id': data.get('message_id', ''),
            'conversation_id': data.get('conversation_id', ''),
            'metadata': data.get('metadata', {}),
            'usage': data.get('usage', {}),
            'created_at': data.get('created_at'),
            'task_id': data.get('task_id')
        }
    
    async def _handle_workflow_started(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工作流开始事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的工作流开始数据
        """
        workflow_data = data.get('data', {})
        
        return {
            'event': 'workflow_started',
            'type': 'progress_update',
            'task_id': data.get('task_id'),
            'workflow_run_id': data.get('workflow_run_id'),
            'workflow_id': workflow_data.get('workflow_id'),
            'progress': 0,
            'stage': 'workflow_started',
            'message': '工作流开始执行',
            'created_at': workflow_data.get('created_at'),
            'metadata': {
                'workflow_data': workflow_data,
                'raw_data': data
            }
        }
    
    async def _handle_workflow_finished(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工作流完成事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的工作流完成数据
        """
        workflow_data = data.get('data', {})
        status = workflow_data.get('status', 'succeeded')
        
        return {
            'event': 'workflow_finished',
            'type': 'progress_update',
            'task_id': data.get('task_id'),
            'workflow_run_id': data.get('workflow_run_id'),
            'status': status,
            'progress': 100 if status == 'succeeded' else 0,
            'stage': 'workflow_finished',
            'message': '工作流执行完成' if status == 'succeeded' else '工作流执行失败',
            'outputs': workflow_data.get('outputs', {}),
            'error': workflow_data.get('error') if status != 'succeeded' else None,
            'created_at': workflow_data.get('created_at'),
            'metadata': {
                'workflow_data': workflow_data,
                'raw_data': data
            }
        }
    
    async def _handle_node_started(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理节点开始事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的节点开始数据
        """
        node_data = data.get('data', {})
        
        return {
            'event': 'node_started',
            'type': 'progress_update',
            'task_id': data.get('task_id'),
            'workflow_run_id': data.get('workflow_run_id'),
            'node_id': node_data.get('node_id'),
            'node_type': node_data.get('node_type'),
            'stage': f"node_{node_data.get('node_type', 'unknown')}_started",
            'message': f"节点 {node_data.get('node_type', 'unknown')} 开始执行",
            'created_at': node_data.get('created_at'),
            'metadata': {
                'node_data': node_data,
                'raw_data': data
            }
        }
    
    async def _handle_node_finished(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理节点完成事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的节点完成数据
        """
        node_data = data.get('data', {})
        status = node_data.get('status', 'succeeded')
        
        return {
            'event': 'node_finished',
            'type': 'progress_update',
            'task_id': data.get('task_id'),
            'workflow_run_id': data.get('workflow_run_id'),
            'node_id': node_data.get('node_id'),
            'node_type': node_data.get('node_type'),
            'status': status,
            'stage': f"node_{node_data.get('node_type', 'unknown')}_finished",
            'message': f"节点 {node_data.get('node_type', 'unknown')} 执行{'完成' if status == 'succeeded' else '失败'}",
            'outputs': node_data.get('outputs', {}),
            'error': node_data.get('error') if status != 'succeeded' else None,
            'execution_metadata': node_data.get('execution_metadata', {}),
            'created_at': node_data.get('created_at'),
            'metadata': {
                'node_data': node_data,
                'raw_data': data
            }
        }
    
    async def _handle_error(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理错误事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的错误数据
        """
        error_status = data.get('status', 500)
        error_code = data.get('code', 'unknown_error')
        error_message = data.get('message', '发生未知错误')
        
        # 根据错误状态码提供用户友好的错误信息
        user_friendly_message = self._get_user_friendly_error_message(error_status, error_code, error_message)
        
        return {
            'event': 'error',
            'type': 'error',
            'status': error_status,
            'code': error_code,
            'message': error_message,
            'user_message': user_friendly_message,
            'task_id': data.get('task_id'),
            'metadata': {
                'raw_data': data
            }
        }
    
    async def _handle_tts_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理TTS消息事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的TTS消息数据
        """
        return {
            'event': 'tts_message',
            'type': 'audio_chunk',
            'audio': data.get('audio', ''),
            'message_id': data.get('message_id', ''),
            'task_id': data.get('task_id'),
            'created_at': data.get('created_at'),
            'metadata': {
                'raw_data': data
            }
        }
    
    async def _handle_tts_message_end(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理TTS消息结束事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的TTS消息结束数据
        """
        return {
            'event': 'tts_message_end',
            'type': 'audio_complete',
            'message_id': data.get('message_id', ''),
            'task_id': data.get('task_id'),
            'audio': data.get('audio', ''),
            'created_at': data.get('created_at'),
            'metadata': {
                'raw_data': data
            }
        }
    
    async def _handle_message_replace(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息替换事件
        
        Args:
            data: 事件数据
            
        Returns:
            Dict[str, Any]: 处理后的消息替换数据
        """
        return {
            'event': 'message_replace',
            'type': 'message_replace',
            'answer': data.get('answer', ''),
            'message_id': data.get('message_id', ''),
            'task_id': data.get('task_id'),
            'created_at': data.get('created_at'),
            'metadata': {
                'raw_data': data
            }
        }
    
    def _get_user_friendly_error_message(self, status: int, code: str, message: str) -> str:
        """
        获取用户友好的错误信息
        
        Args:
            status: HTTP状态码
            code: 错误代码
            message: 原始错误信息
            
        Returns:
            str: 用户友好的错误信息
        """
        if status == 400:
            return "请求参数有误，请检查输入内容"
        elif status == 401:
            return "身份验证失败，请检查API密钥"
        elif status == 403:
            return "访问权限不足，请联系管理员"
        elif status == 404:
            return "请求的资源不存在"
        elif status == 413:
            return "上传的文件过大，请减小文件大小"
        elif status == 429:
            return "请求过于频繁，请稍后再试"
        elif status >= 500:
            return "服务器内部错误，请稍后重试"
        else:
            return f"发生错误: {message}"
    
    def get_supported_events(self) -> List[str]:
        """
        获取支持的事件类型列表
        
        Returns:
            List[str]: 支持的事件类型
        """
        return list(self.event_handlers.keys())
    
    async def validate_event_data(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        验证事件数据的有效性
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            bool: 数据是否有效
        """
        try:
            if event_type not in self.event_handlers:
                return False
            
            # 基本字段验证
            if not isinstance(data, dict):
                return False
            
            # 根据事件类型进行特定验证
            if event_type in ['message', 'message_end']:
                return 'message_id' in data
            elif event_type in ['workflow_started', 'workflow_finished']:
                return 'task_id' in data and 'workflow_run_id' in data
            elif event_type in ['node_started', 'node_finished']:
                return 'task_id' in data and 'workflow_run_id' in data
            elif event_type == 'error':
                return 'status' in data or 'code' in data or 'message' in data
            
            return True
            
        except Exception as e:
            logger.error(f"验证事件数据异常: {e}")
            return False


@dataclass
class DifyChatRequest:
    """Dify聊天请求模型"""
    query: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    response_mode: str = "streaming"  # "streaming" or "blocking"
    conversation_id: Optional[str] = None
    user: str = "default_user"
    files: List[Dict[str, Any]] = field(default_factory=list)
    auto_generate_name: bool = True


@dataclass
class DifyMessage:
    """Dify消息模型"""
    event: str
    task_id: Optional[str] = None
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    answer: Optional[str] = None
    created_at: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DifyFileUpload:
    """Dify文件上传模型"""
    file: bytes
    user: str
    filename: str
    content_type: str = "application/xml"


@dataclass
class ConversationSession:
    """对话会话模型"""
    session_id: str
    user_id: str
    conversation_id: Optional[str]  # Dify conversation ID
    messages: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    status: str  # "active", "paused", "completed"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """聊天消息模型"""
    id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationSessionManager:
    """对话会话管理器"""
    
    def __init__(self, redis_client=None):
        """
        初始化会话管理器
        
        Args:
            redis_client: Redis客户端，如果为None则使用内存存储
        """
        self.redis = redis_client
        self.session_timeout = 3600  # 1小时
        self.memory_sessions = {}  # 内存存储备选方案
        
        logger.info(f"ConversationSessionManager初始化完成，存储方式: {'Redis' if redis_client else '内存'}")
    
    async def create_session(self, user_id: str) -> str:
        """
        创建新的对话会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 会话ID
        """
        session_id = f"conv_{uuid.uuid4().hex[:12]}"
        session_data = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            conversation_id=None,  # Dify conversation ID将在首次对话时生成
            messages=[],
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status='active'
        )
        
        await self._store_session(session_id, session_data)
        logger.info(f"创建新会话: session_id={session_id}, user_id={user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[ConversationSession]: 会话数据
        """
        try:
            if self.redis:
                session_data = await self.redis.get(f"session:{session_id}")
                if session_data:
                    data_dict = json.loads(session_data)
                    return self._dict_to_session(data_dict)
            else:
                return self.memory_sessions.get(session_id)
            
            return None
            
        except Exception as e:
            logger.error(f"获取会话失败: session_id={session_id}, error={e}")
            return None
    
    async def update_conversation_id(self, session_id: str, conversation_id: str):
        """
        更新会话的Dify conversation_id
        
        Args:
            session_id: 会话ID
            conversation_id: Dify对话ID
        """
        session = await self.get_session(session_id)
        if session:
            session.conversation_id = conversation_id
            session.last_activity = datetime.utcnow()
            await self._store_session(session_id, session)
            logger.info(f"更新会话conversation_id: session_id={session_id}, conversation_id={conversation_id}")
    
    async def add_message(self, session_id: str, message: ChatMessage):
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            message: 聊天消息
        """
        session = await self.get_session(session_id)
        if session:
            message_dict = {
                'id': message.id,
                'session_id': message.session_id,
                'role': message.role,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata
            }
            session.messages.append(message_dict)
            session.last_activity = datetime.utcnow()
            await self._store_session(session_id, session)
            logger.debug(f"添加消息到会话: session_id={session_id}, role={message.role}")
    
    async def get_conversation_context(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取对话上下文
        
        Args:
            session_id: 会话ID
            limit: 消息数量限制
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        session = await self.get_session(session_id)
        if session and session.messages:
            # 返回最近的消息
            recent_messages = session.messages[-limit:] if len(session.messages) > limit else session.messages
            logger.debug(f"获取对话上下文: session_id={session_id}, messages={len(recent_messages)}")
            return recent_messages
        return []
    
    async def get_dify_conversation_id(self, session_id: str) -> Optional[str]:
        """
        获取Dify conversation_id
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[str]: Dify对话ID
        """
        session = await self.get_session(session_id)
        return session.conversation_id if session else None
    
    async def pause_session(self, session_id: str):
        """
        暂停会话
        
        Args:
            session_id: 会话ID
        """
        session = await self.get_session(session_id)
        if session:
            session.status = 'paused'
            session.last_activity = datetime.utcnow()
            await self._store_session(session_id, session)
            logger.info(f"暂停会话: session_id={session_id}")
    
    async def resume_session(self, session_id: str):
        """
        恢复会话
        
        Args:
            session_id: 会话ID
        """
        session = await self.get_session(session_id)
        if session:
            session.status = 'active'
            session.last_activity = datetime.utcnow()
            await self._store_session(session_id, session)
            logger.info(f"恢复会话: session_id={session_id}")
    
    async def complete_session(self, session_id: str):
        """
        完成会话
        
        Args:
            session_id: 会话ID
        """
        session = await self.get_session(session_id)
        if session:
            session.status = 'completed'
            session.last_activity = datetime.utcnow()
            await self._store_session(session_id, session)
            logger.info(f"完成会话: session_id={session_id}")
    
    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            if self.redis:
                # Redis会自动处理过期，这里可以添加额外的清理逻辑
                pass
            else:
                # 清理内存中的过期会话
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.memory_sessions.items():
                    time_diff = (current_time - session.last_activity).total_seconds()
                    if time_diff > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.memory_sessions[session_id]
                    logger.info(f"清理过期会话: session_id={session_id}")
                    
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
    
    async def cleanup_all_sessions(self):
        """
        清理所有会话 - 强制清理方法
        
        这个方法会清理所有会话，不管是否过期，通常在应用关闭时使用
        """
        try:
            logger.info("开始清理所有会话")
            
            if self.redis:
                # 清理Redis中的所有会话
                try:
                    # 获取所有会话键
                    session_keys = await self.redis.keys("session:*")
                    if session_keys:
                        await self.redis.delete(*session_keys)
                        logger.info(f"清理Redis中的 {len(session_keys)} 个会话")
                except Exception as e:
                    logger.warning(f"清理Redis会话失败: {e}")
            else:
                # 清理内存中的所有会话
                session_count = len(self.memory_sessions)
                self.memory_sessions.clear()
                logger.info(f"清理内存中的 {session_count} 个会话")
            
            logger.info("所有会话清理完成")
            
        except Exception as e:
            logger.error(f"清理所有会话失败: {e}")
            raise
    
    async def _store_session(self, session_id: str, session: ConversationSession):
        """
        存储会话数据
        
        Args:
            session_id: 会话ID
            session: 会话数据
        """
        try:
            if self.redis:
                session_dict = self._session_to_dict(session)
                await self.redis.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    json.dumps(session_dict, ensure_ascii=False)
                )
            else:
                self.memory_sessions[session_id] = session
                
        except Exception as e:
            logger.error(f"存储会话失败: session_id={session_id}, error={e}")
            # 降级到内存存储
            self.memory_sessions[session_id] = session
    
    def _session_to_dict(self, session: ConversationSession) -> Dict[str, Any]:
        """将会话对象转换为字典"""
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'conversation_id': session.conversation_id,
            'messages': session.messages,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'status': session.status,
            'metadata': session.metadata
        }
    
    def _dict_to_session(self, data: Dict[str, Any]) -> ConversationSession:
        """将字典转换为会话对象"""
        return ConversationSession(
            session_id=data['session_id'],
            user_id=data['user_id'],
            conversation_id=data.get('conversation_id'),
            messages=data.get('messages', []),
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            status=data.get('status', 'active'),
            metadata=data.get('metadata', {})
        )


class ModeSelector:
    """AI服务模式选择器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模式选择器
        
        Args:
            config: AI服务配置
        """
        self.mock_mode = config.get('mock_mode', True)
        self.dify_config = config.get('dify_config', config)
        self.current_mode = 'mock' if self.mock_mode else 'dify'
        
        logger.info(f"ModeSelector初始化完成，当前模式: {self.current_mode}")
    
    def get_handler(self) -> Union['MockHandler', 'DifyHandler']:
        """
        获取当前模式的处理器
        
        Returns:
            Union[MockHandler, DifyHandler]: 对应模式的处理器
        """
        if self.current_mode == 'mock':
            return MockHandler()
        else:
            return DifyHandler(self.dify_config)
    
    def switch_to_mock(self, reason: str = "fallback"):
        """
        切换到Mock模式
        
        Args:
            reason: 切换原因
        """
        old_mode = self.current_mode
        self.current_mode = 'mock'
        
        # 详细记录模式切换信息
        from datetime import datetime
        logger.warning(f"AI服务模式切换详情:")
        logger.warning(f"  切换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.warning(f"  原模式: {old_mode}")
        logger.warning(f"  新模式: {self.current_mode}")
        logger.warning(f"  切换原因: {reason}")
        
        # 记录切换原因的详细分类
        reason_details = {
            "fallback": "Dify服务不可用，自动降级",
            "network_error": "网络连接异常",
            "auth_error": "认证失败",
            "rate_limit": "请求频率限制",
            "server_error": "服务器内部错误",
            "timeout": "请求超时",
            "manual": "手动切换"
        }
        
        detailed_reason = reason_details.get(reason, f"未知原因: {reason}")
        logger.warning(f"  详细原因: {detailed_reason}")
        
        # 记录当前Dify配置状态（不包含敏感信息）
        if hasattr(self, 'dify_config') and self.dify_config:
            logger.warning(f"  Dify配置状态:")
            logger.warning(f"    API URL: {self.dify_config.get('api_url', '未配置')}")
            logger.warning(f"    应用类型: {self.dify_config.get('app_type', '未知')}")
            logger.warning(f"    配置完整性: {'完整' if all(k in self.dify_config for k in ['api_url', 'api_key', 'app_type']) else '不完整'}")
        
        # 记录影响范围
        logger.warning(f"  影响: 后续AI请求将使用Mock数据响应")
    
    def switch_to_dify(self):
        """切换到Dify模式"""
        if not self.mock_mode:
            self.current_mode = 'dify'
            logger.info("已切换到Dify模式")
    
    def is_mock_mode(self) -> bool:
        """检查是否为Mock模式"""
        return self.current_mode == 'mock'


class MockHandler:
    """Mock模式处理器"""
    
    def __init__(self):
        """初始化Mock处理器"""
        self.mock_responses = [
            "好的，我已经分析了您上传的文件。请描述一下您希望生成的测试用例类型和测试场景。",
            "了解了您的需求。关于登录功能测试，您希望覆盖哪些场景：1.正常登录 2.密码错误 3.账号不存在 4.验证码校验？",
            "很好！我还需要了解一些细节：您希望测试哪些浏览器兼容性？是否需要包含移动端测试？",
            "明白了。最后确认一下测试数据：您希望使用真实的测试账号还是模拟数据？如果准备好了，请回复'开始生成'。",
            "收到！我现在有足够的信息来生成高质量的测试用例了。请告诉我是否可以开始生成？"
        ]
        
        logger.info("MockHandler初始化完成")


class DifyHandler:
    """Dify API处理器 - 增强版本支持异步操作和完整的API集成"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Dify处理器
        
        Args:
            config: Dify配置
        """
        self.base_url = config.get('dify_url', 'https://api.dify.ai/v1')
        self.api_token = config.get('dify_token', '')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.stream_mode = config.get('stream_mode', True)
        
        # 初始化进度跟踪和事件处理
        self.progress_tracker = ProgressTracker()
        self.event_processor = EventProcessor(self.progress_tracker)
        
        # 初始化流式处理器
        self.stream_processor = StreamProcessor(
            progress_tracker=self.progress_tracker,
            event_processor=self.event_processor
        )
        
        # 初始化流式客户端
        self.streaming_client = DifyStreamingClient(self)
        
        # 设置同步请求会话
        self.session = requests.Session()
        self._setup_session()
        
        # 异步会话将在需要时创建
        self._async_session = None
        
        logger.info(f"DifyHandler初始化完成，API URL: {self.base_url}")
    
    def _setup_session(self):
        """配置HTTP会话"""
        if not self.api_token:
            logger.warning("Dify API token未配置")
            
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI-TestCase-Generator/1.0'
        })
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """
        获取异步HTTP会话 - 修复连接泄漏问题
        
        原问题：每次调用都创建新的ClientSession，导致连接泄漏
        解决方案：使用单例模式管理ClientSession，确保正确关闭
        
        Returns:
            aiohttp.ClientSession: 优化的异步HTTP会话
        """
        if self._async_session is None or self._async_session.closed:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'AI-TestCase-Generator/1.0'
            }
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            # 使用连接器配置来优化连接管理
            connector = aiohttp.TCPConnector(
                limit=100,  # 总连接池大小
                limit_per_host=30,  # 每个主机的连接数
                ttl_dns_cache=300,  # DNS缓存时间（秒）
                use_dns_cache=True,  # 启用DNS缓存
                keepalive_timeout=30,  # 保持连接时间（秒）
                enable_cleanup_closed=True,  # 启用清理已关闭的连接
                force_close=False,  # 不强制关闭连接，允许复用
                ssl=False  # 根据实际需要配置SSL
            )
            
            self._async_session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            )
            
            logger.debug(f"创建新的异步HTTP会话: connector_limit={connector.limit}, limit_per_host={connector.limit_per_host}")
        
        return self._async_session
    
    def get_streaming_client(self) -> 'DifyStreamingClient':
        """获取流式客户端"""
        return self.streaming_client
    
    def get_progress_tracker(self) -> ProgressTracker:
        """获取进度跟踪器"""
        return self.progress_tracker
    
    def get_event_processor(self) -> EventProcessor:
        """获取事件处理器"""
        return self.event_processor
    
    def add_progress_callback(self, callback):
        """添加进度更新回调"""
        self.progress_tracker.add_progress_callback(callback)
    
    def add_message_completion_callback(self, callback):
        """添加消息完成回调"""
        self.event_processor.add_message_completion_callback(callback)
    
    def add_error_callback(self, callback):
        """添加错误回调"""
        self.event_processor.add_error_callback(callback)
    
    def get_workflow_progress(self, workflow_run_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流进度"""
        return self.progress_tracker.get_workflow_progress(workflow_run_id)
    
    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """获取所有工作流进度"""
        return self.progress_tracker.get_all_workflows()
    
    def cleanup_finished_workflows(self, max_age_hours: int = 24):
        """清理已完成的工作流"""
        self.progress_tracker.cleanup_finished_workflows(max_age_hours)
    
    def send_message(self, conversation_id: str, message: str, context: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
        """
        发送消息到Dify (同步版本)
        
        Args:
            conversation_id: 对话ID
            message: 消息内容
            context: 对话上下文
            stream: 是否使用流式模式
            
        Returns:
            Dict[str, Any]: Dify响应
        """
        try:
            request_data = self._build_chat_request(
                conversation_id=conversation_id,
                message=message,
                context=context,
                stream=stream
            )
            
            logger.debug(f"发送Dify消息: conversation_id={conversation_id}, stream={stream}")
            
            response = self.session.post(
                f'{self.base_url}/chat-messages',
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Dify消息发送成功: message_id={result.get('message_id', 'unknown')}")
                return result
            else:
                error_msg = f"Dify API请求失败: {response.status_code}"
                logger.error(f"{error_msg}, response: {response.text}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Dify消息发送异常: {e}")
            raise
    
    async def send_message_async(self, 
                                conversation_id: str, 
                                message: str, 
                                context: Dict[str, Any], 
                                stream: bool = False) -> Union[Dict[str, Any], AsyncGenerator]:
        """
        发送消息到Dify (异步版本) - 增强错误处理和重试机制
        
        原问题：连接使用后没有正确清理，导致"Unclosed client session"错误
        解决方案：使用上下文管理器确保连接正确关闭，添加重试机制和详细错误处理
        
        Args:
            conversation_id: 对话ID
            message: 消息内容
            context: 对话上下文
            stream: 是否使用流式模式
            
        Returns:
            Union[Dict[str, Any], AsyncGenerator]: Dify响应或流式生成器
        """
        import asyncio
        import aiohttp
        
        max_retries = self.max_retries
        base_delay = 1.0  # 基础延迟时间（秒）
        
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_async_session()
                request_data = self._build_chat_request(
                    conversation_id=conversation_id,
                    message=message,
                    context=context,
                    stream=stream
                )
                
                logger.debug(f"异步发送Dify消息 (尝试 {attempt + 1}/{max_retries + 1}): conversation_id={conversation_id}, stream={stream}")
                
                # 使用上下文管理器确保连接正确关闭
                async with session.post(
                    f'{self.base_url}/chat-messages',
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        if stream:
                            # 使用StreamProcessor处理流式响应
                            logger.info(f"Dify异步流式消息发送成功: conversation_id={conversation_id}")
                            return self.stream_processor.process_stream(response)
                        else:
                            result = await response.json()
                            logger.info(f"Dify异步消息发送成功: message_id={result.get('message_id', 'unknown')}, conversation_id={result.get('conversation_id', conversation_id)}")
                            return result
                    else:
                        error_text = await response.text()
                        error_msg = f"Dify API请求失败: HTTP {response.status}"
                        
                        # 根据HTTP状态码决定是否重试
                        if response.status in [429, 500, 502, 503, 504] and attempt < max_retries:
                            # 可重试的错误：限流、服务器错误
                            delay = base_delay * (2 ** attempt)  # 指数退避
                            logger.warning(f"{error_msg}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                            logger.debug(f"响应内容: {error_text}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # 不可重试的错误或重试次数用完
                            logger.error(f"{error_msg}, response: {error_text}")
                            if response.status == 404 and 'conversation' in error_text.lower():
                                # 特殊处理对话不存在的错误
                                raise ConversationNotFoundError(f"对话不存在: {conversation_id}")
                            else:
                                raise DifyAPIError(f"{error_msg}: {error_text}", status_code=response.status)
                        
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                # 网络连接错误，可以重试
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"网络连接异常: {type(e).__name__} - {e}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"网络连接异常，重试次数用完: {type(e).__name__} - {e}")
                    raise NetworkError(f"网络连接失败: {e}")
                    
            except (ConversationNotFoundError, DifyAPIError) as e:
                # 业务逻辑错误，不重试
                logger.error(f"Dify业务异常: {type(e).__name__} - {e}")
                raise
                
            except Exception as e:
                # 其他未知错误
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"未知异常: {type(e).__name__} - {e}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Dify异步消息发送异常，重试次数用完: {type(e).__name__} - {e}")
                    raise DifyAPIError(f"消息发送失败: {e}")
        
        # 如果所有重试都失败了（理论上不会到达这里）
        raise DifyAPIError("消息发送失败：所有重试尝试都已用完")
    
    def _build_chat_request(self, 
                           conversation_id: str, 
                           message: str, 
                           context: Dict[str, Any], 
                           stream: bool = False) -> Dict[str, Any]:
        """
        构建聊天请求数据
        
        Args:
            conversation_id: 对话ID
            message: 消息内容
            context: 对话上下文
            stream: 是否流式模式
            
        Returns:
            Dict[str, Any]: 请求数据
        """
        # 根据Dify文档和实际使用格式构建请求
        request_data = {
            'query': message,  # 用户输入/提问内容
            'inputs': {},  # App定义的变量值
            'response_mode': 'streaming' if stream else 'blocking',
            'user': 'ai-testcase-generator-user',  # 固定的用户标识
            'auto_generate_name': True
        }
        
        # 如果有conversation_id，添加到请求中
        if conversation_id:
            request_data['conversation_id'] = conversation_id
        
        # 添加文件引用（如果有）
        files = context.get('files', [])
        if files:
            request_data['files'] = files
        
        # 从context中获取Dify系统参数并添加到inputs中
        dify_system_params = context.get('dify_system_params', {})
        if dify_system_params:
            # 将系统参数添加到inputs中，保持sys.前缀
            for key, value in dify_system_params.items():
                if key.startswith('sys.'):
                    request_data['inputs'][key] = value
                else:
                    request_data['inputs'][f'sys.{key}'] = value
            logger.debug(f"添加Dify系统参数到请求: {dify_system_params}")
        
        # 如果有其他输入变量，添加到inputs中
        if context.get('inputs'):
            request_data['inputs'].update(context['inputs'])
        
        logger.debug(f"构建的请求数据: query='{message[:50]}...', conversation_id={conversation_id}, inputs_keys={list(request_data['inputs'].keys())}")
        
        return request_data
    
    
    async def upload_file(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """
        上传文件到Dify - 增强错误处理和重试机制
        
        Args:
            file_path: 文件路径
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 上传响应
        """
        import asyncio
        import aiohttp
        import os
        
        max_retries = self.max_retries
        base_delay = 1.0  # 基础延迟时间（秒）
        
        # 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件大小用于日志
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_async_session()
                
                # 读取文件内容
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # 创建multipart/form-data
                data = aiohttp.FormData()
                data.add_field('file', file_content, filename=filename, content_type='application/xml')
                data.add_field('user', user_id)
                
                logger.debug(f"上传文件到Dify (尝试 {attempt + 1}/{max_retries + 1}): {filename} ({file_size} bytes), user: {user_id}")
                
                # 移除Content-Type头，让aiohttp自动设置multipart边界
                headers = {k: v for k, v in session.headers.items() if k.lower() != 'content-type'}
                
                # 使用上下文管理器确保连接正确关闭
                async with session.post(
                    f'{self.base_url}/files/upload',
                    data=data,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"文件上传成功: file_id={result.get('id', 'unknown')}, filename={filename}")
                        return result
                    else:
                        error_text = await response.text()
                        error_msg = f"文件上传失败: HTTP {response.status}"
                        
                        # 根据HTTP状态码决定是否重试
                        if response.status in [429, 500, 502, 503, 504] and attempt < max_retries:
                            # 可重试的错误：限流、服务器错误
                            delay = base_delay * (2 ** attempt)  # 指数退避
                            logger.warning(f"{error_msg}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                            logger.debug(f"响应内容: {error_text}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # 不可重试的错误或重试次数用完
                            logger.error(f"{error_msg}, response: {error_text}")
                            if response.status == 413:
                                raise DifyAPIError(f"文件过大: {filename} ({file_size} bytes)", status_code=response.status)
                            elif response.status == 400:
                                raise DifyAPIError(f"文件格式不支持: {filename}", status_code=response.status)
                            else:
                                raise DifyAPIError(f"{error_msg}: {error_text}", status_code=response.status)
                        
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                # 网络连接错误，可以重试
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"文件上传网络异常: {type(e).__name__} - {e}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"文件上传网络异常，重试次数用完: {type(e).__name__} - {e}")
                    raise NetworkError(f"文件上传网络连接失败: {e}")
                    
            except (FileNotFoundError, DifyAPIError) as e:
                # 业务逻辑错误，不重试
                logger.error(f"文件上传业务异常: {type(e).__name__} - {e}")
                raise
                
            except Exception as e:
                # 其他未知错误
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"文件上传未知异常: {type(e).__name__} - {e}, 将在 {delay:.1f}s 后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"文件上传异常，重试次数用完: {type(e).__name__} - {e}")
                    raise DifyAPIError(f"文件上传失败: {e}")
        
        # 如果所有重试都失败了（理论上不会到达这里）
        raise DifyAPIError("文件上传失败：所有重试尝试都已用完")
    
    def test_connection(self) -> bool:
        """
        测试Dify连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 使用parameters端点进行连接测试
            response = self.session.get(
                f'{self.base_url}/parameters',
                timeout=5
            )
            
            success = response.status_code == 200
            if success:
                logger.info("Dify连接测试成功")
            else:
                logger.warning(f"Dify连接测试失败: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Dify连接测试异常: {e}")
            return False
    
    async def close(self):
        """关闭异步会话 - 确保资源清理"""
        try:
            # 关闭异步会话
            if self._async_session and not self._async_session.closed:
                await self._async_session.close()
                logger.debug("Dify异步会话已关闭")
                
                # 等待连接器完全关闭
                if hasattr(self._async_session, 'connector') and self._async_session.connector:
                    await self._async_session.connector.close()
                    logger.debug("Dify连接器已关闭")
            
            # 关闭同步会话
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.debug("Dify同步会话已关闭")
            
            # 清理进度跟踪器中的过期工作流
            if hasattr(self, 'progress_tracker') and self.progress_tracker:
                try:
                    self.progress_tracker.cleanup_finished_workflows(max_age_hours=0)  # 立即清理所有已完成的工作流
                    logger.debug("进度跟踪器已清理")
                except Exception as e:
                    logger.warning(f"清理进度跟踪器失败: {e}")
            
            logger.info("DifyHandler资源清理完成")
            
        except Exception as e:
            logger.error(f"DifyHandler资源清理异常: {e}")
            raise
    
    def __del__(self):
        """析构函数 - 确保资源清理"""
        try:
            # 清理异步会话
            if hasattr(self, '_async_session') and self._async_session and not self._async_session.closed:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，创建任务异步关闭
                        loop.create_task(self._async_session.close())
                        if hasattr(self._async_session, 'connector') and self._async_session.connector:
                            loop.create_task(self._async_session.connector.close())
                    else:
                        # 如果事件循环未运行，同步关闭
                        loop.run_until_complete(self._async_session.close())
                        if hasattr(self._async_session, 'connector') and self._async_session.connector:
                            loop.run_until_complete(self._async_session.connector.close())
                    logger.debug("析构函数中关闭Dify异步会话成功")
                except Exception as e:
                    logger.warning(f"析构函数中关闭异步会话失败: {e}")
            
            # 清理同步会话
            if hasattr(self, 'session') and self.session:
                try:
                    self.session.close()
                    logger.debug("析构函数中关闭Dify同步会话成功")
                except Exception as e:
                    logger.warning(f"析构函数中关闭同步会话失败: {e}")
            
            # 清理其他资源
            if hasattr(self, 'progress_tracker') and self.progress_tracker:
                try:
                    # 在析构函数中只做简单清理，避免复杂操作
                    self.progress_tracker.workflows.clear()
                    logger.debug("析构函数中清理进度跟踪器成功")
                except Exception as e:
                    logger.warning(f"析构函数中清理进度跟踪器失败: {e}")
                    
        except Exception as e:
            # 析构函数中不应该抛出异常
            try:
                logger.warning(f"析构函数执行失败: {e}")
            except:
                # 如果连日志都无法记录，就静默忽略
                pass


class DifyStreamingClient:
    """专门处理Dify流式API调用的客户端"""
    
    def __init__(self, dify_handler: DifyHandler):
        """
        初始化Dify流式客户端
        
        Args:
            dify_handler: Dify处理器实例
        """
        self.dify_handler = dify_handler
        self.active_streams = {}  # 活跃的流式连接
        
        logger.info("DifyStreamingClient初始化完成")
    
    async def send_streaming_message(self, message: str, conversation_id: str = None, context: Dict[str, Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        发送流式消息到Dify
        
        Args:
            message: 消息内容
            conversation_id: 对话ID（可选）
            context: 对话上下文（可选）
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        stream_id = f"dify_stream_{uuid.uuid4().hex[:8]}"
        
        try:
            # 记录活跃流
            self.active_streams[stream_id] = {
                'conversation_id': conversation_id,
                'started_at': datetime.utcnow(),
                'status': 'active'
            }
            
            logger.info(f"开始Dify流式消息发送: stream_id={stream_id}, conversation_id={conversation_id}")
            
            # 调用DifyHandler的异步流式方法
            stream_response = await self.dify_handler.send_message_async(
                conversation_id=conversation_id,
                message=message,
                context=context or {},
                stream=True
            )
            
            # 处理流式响应
            async for chunk in self._handle_stream_response(stream_response):
                yield chunk
                
        except Exception as e:
            logger.error(f"Dify流式消息发送异常: stream_id={stream_id}, error={e}")
            yield {
                'event': 'error',
                'error': 'dify_stream_error',
                'message': str(e),
                'user_message': 'AI服务响应异常，请稍后重试'
            }
            
        finally:
            # 清理活跃流记录
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'completed'
                self.active_streams[stream_id]['completed_at'] = datetime.utcnow()
                
                # 延迟清理
                asyncio.create_task(self._cleanup_stream(stream_id, delay=300))
    
    async def _handle_stream_response(self, stream_response) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理流式响应数据
        
        Args:
            stream_response: 流式响应生成器
            
        Yields:
            Dict[str, Any]: 处理后的流式数据
        """
        try:
            if hasattr(stream_response, '__aiter__'):
                # 异步生成器
                async for chunk in stream_response:
                    if chunk:
                        processed_chunk = self._parse_stream_chunk(chunk)
                        if processed_chunk:
                            yield processed_chunk
            else:
                # 普通响应，转换为流式格式
                content = stream_response.get('answer', '') if isinstance(stream_response, dict) else str(stream_response)
                
                # 分块发送
                chunk_size = 5
                for i in range(0, len(content), chunk_size):
                    chunk_content = content[i:i + chunk_size]
                    yield {
                        'event': 'message',
                        'content': chunk_content,
                        'message_id': stream_response.get('message_id', f"msg_{uuid.uuid4().hex[:8]}"),
                        'conversation_id': stream_response.get('conversation_id')
                    }
                    await asyncio.sleep(0.05)  # 模拟流式延迟
                
                # 发送结束事件
                yield {
                    'event': 'message_end',
                    'message_id': stream_response.get('message_id', f"msg_{uuid.uuid4().hex[:8]}"),
                    'conversation_id': stream_response.get('conversation_id'),
                    'metadata': stream_response.get('metadata', {})
                }
                
        except Exception as e:
            logger.error(f"处理流式响应异常: {e}")
            yield {
                'event': 'error',
                'error': 'stream_processing_error',
                'message': str(e)
            }
    
    def _parse_stream_chunk(self, chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析流式数据块
        
        Args:
            chunk: 原始数据块
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的数据块
        """
        try:
            # 如果chunk已经是正确格式，直接返回
            if isinstance(chunk, dict) and 'event' in chunk:
                return chunk
            
            # 尝试解析其他格式的数据
            if isinstance(chunk, dict):
                # 根据数据内容推断事件类型
                if 'answer' in chunk:
                    return {
                        'event': 'message',
                        'content': chunk.get('answer', ''),
                        'message_id': chunk.get('message_id'),
                        'conversation_id': chunk.get('conversation_id')
                    }
                elif 'workflow_run_id' in chunk:
                    return {
                        'event': 'workflow_started',
                        'workflow_run_id': chunk.get('workflow_run_id'),
                        'progress': 0
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"解析流式数据块失败: {e}")
            return None
    
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
                logger.debug(f"清理Dify流式连接记录: stream_id={stream_id}")
        except Exception as e:
            logger.error(f"清理Dify流式连接记录失败: stream_id={stream_id}, error={e}")
    
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
            logger.info(f"清理所有Dify流式连接记录: {stream_count} 个")
        except Exception as e:
            logger.error(f"清理所有Dify流式连接记录失败: {e}")


class DifyErrorHandler:
    """Dify错误处理器 - 实现错误分类、重试机制和自动降级"""
    
    def __init__(self, mode_selector: 'ModeSelector'):
        """
        初始化错误处理器
        
        Args:
            mode_selector: 模式选择器，用于降级切换
        """
        self.mode_selector = mode_selector
        self.retry_count = {}  # 记录每个请求的重试次数
        self.max_retries = 3
        self.base_delay = 1.0  # 基础延迟时间（秒）
        self.max_delay = 30.0  # 最大延迟时间（秒）
        self.exponential_base = 2  # 指数退避基数
        
        # 错误分类配置
        self.client_errors = {400, 401, 403, 404, 413, 422}  # 4xx客户端错误，不重试
        self.server_errors = {500, 502, 503, 504}  # 5xx服务器错误，需要重试
        
        logger.info("DifyErrorHandler初始化完成")


class ErrorRecoveryManager:
    """错误恢复管理器 - 实现网络异常重试、会话恢复和资源清理"""
    
    def __init__(self, session_service, ai_service):
        """
        初始化错误恢复管理器
        
        Args:
            session_service: 会话服务实例
            ai_service: AI服务实例
        """
        self.session_service = session_service
        self.ai_service = ai_service
        
        # 网络重试配置
        self.network_retry_config = {
            'max_retries': 5,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'exponential_base': 2,
            'jitter': True  # 添加随机抖动避免雷群效应
        }
        
        # 会话恢复配置
        self.session_recovery_config = {
            'auto_recovery_enabled': True,
            'recovery_timeout': 30.0,
            'max_recovery_attempts': 3
        }
        
        # 资源清理配置
        self.cleanup_config = {
            'cleanup_timeout': 10.0,
            'force_cleanup': True,
            'cleanup_retry_count': 2
        }
        
        logger.info("ErrorRecoveryManager初始化完成")
    
    async def handle_network_error(self, 
                                  error: Exception, 
                                  operation_func,
                                  operation_args: tuple = (),
                                  operation_kwargs: dict = None,
                                  context: dict = None) -> dict:
        """
        处理网络异常的重试策略
        
        Args:
            error: 网络异常
            operation_func: 需要重试的操作函数
            operation_args: 操作函数的位置参数
            operation_kwargs: 操作函数的关键字参数
            context: 上下文信息
            
        Returns:
            dict: 重试结果
        """
        import random
        from datetime import datetime
        
        operation_kwargs = operation_kwargs or {}
        context = context or {}
        
        config = self.network_retry_config
        operation_name = getattr(operation_func, '__name__', 'unknown_operation')
        
        logger.warning(f"网络异常恢复开始:")
        logger.warning(f"  操作: {operation_name}")
        logger.warning(f"  异常: {type(error).__name__} - {error}")
        logger.warning(f"  最大重试次数: {config['max_retries']}")
        
        for attempt in range(config['max_retries']):
            try:
                # 计算延迟时间（指数退避 + 随机抖动）
                base_delay = min(
                    config['base_delay'] * (config['exponential_base'] ** attempt),
                    config['max_delay']
                )
                
                if config['jitter']:
                    # 添加±25%的随机抖动
                    jitter = random.uniform(-0.25, 0.25) * base_delay
                    delay = max(0.1, base_delay + jitter)
                else:
                    delay = base_delay
                
                if attempt > 0:
                    logger.info(f"  第 {attempt + 1} 次重试，延迟 {delay:.2f}s")
                    await asyncio.sleep(delay)
                
                # 执行操作
                result = await operation_func(*operation_args, **operation_kwargs)
                
                logger.info(f"  网络异常恢复成功，尝试次数: {attempt + 1}")
                return {
                    'success': True,
                    'result': result,
                    'attempts': attempt + 1,
                    'recovery_time': delay * attempt if attempt > 0 else 0
                }
                
            except Exception as retry_error:
                logger.warning(f"  第 {attempt + 1} 次重试失败: {type(retry_error).__name__} - {retry_error}")
                
                # 如果是最后一次尝试，记录详细错误
                if attempt == config['max_retries'] - 1:
                    logger.error(f"  网络异常恢复失败，已用完所有重试次数")
                    logger.error(f"  最终错误: {type(retry_error).__name__} - {retry_error}")
                    
                    return {
                        'success': False,
                        'error': retry_error,
                        'attempts': attempt + 1,
                        'recovery_failed': True
                    }
        
        # 理论上不会到达这里
        return {
            'success': False,
            'error': error,
            'attempts': config['max_retries'],
            'recovery_failed': True
        }
    
    async def recover_expired_session(self, session_id: str, context: dict = None) -> dict:
        """
        会话过期的自动恢复
        
        Args:
            session_id: 过期的会话ID
            context: 恢复上下文信息
            
        Returns:
            dict: 恢复结果
        """
        from datetime import datetime
        
        context = context or {}
        config = self.session_recovery_config
        
        if not config['auto_recovery_enabled']:
            logger.warning(f"会话自动恢复已禁用: {session_id}")
            return {
                'success': False,
                'reason': 'auto_recovery_disabled',
                'new_session_id': None
            }
        
        logger.info(f"会话过期自动恢复开始:")
        logger.info(f"  过期会话ID: {session_id}")
        logger.info(f"  恢复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for attempt in range(config['max_recovery_attempts']):
            try:
                logger.info(f"  第 {attempt + 1} 次恢复尝试")
                
                # 1. 获取原会话的基本信息（如果还能获取到）
                old_session_data = None
                try:
                    old_session_data = self.session_service.get_session_data(session_id)
                    if old_session_data:
                        logger.info(f"    成功获取原会话数据")
                    else:
                        logger.warning(f"    原会话数据已不可用")
                except Exception as e:
                    logger.warning(f"    获取原会话数据失败: {e}")
                
                # 2. 创建新会话
                new_session_id = self.session_service.create_session()
                logger.info(f"    创建新会话: {new_session_id}")
                
                # 3. 尝试恢复关键数据
                if old_session_data and isinstance(old_session_data, dict):
                    recovery_data = {}
                    
                    # 恢复文件信息
                    if 'files_info' in old_session_data:
                        recovery_data['files_info'] = old_session_data['files_info']
                        logger.info(f"    恢复文件信息: {len(old_session_data['files_info'])} 个文件")
                    
                    # 恢复配置信息
                    if 'config' in old_session_data:
                        recovery_data['config'] = old_session_data['config']
                        logger.info(f"    恢复配置信息")
                    
                    # 恢复聊天历史（最近的几条）
                    if 'chat_history' in old_session_data:
                        chat_history = old_session_data['chat_history']
                        if isinstance(chat_history, list) and len(chat_history) > 0:
                            # 只恢复最近的5条消息
                            recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
                            recovery_data['chat_history'] = recent_history
                            logger.info(f"    恢复聊天历史: {len(recent_history)} 条消息")
                    
                    # 更新新会话数据
                    if recovery_data:
                        success = self.session_service.update_session_data(new_session_id, recovery_data)
                        if success:
                            logger.info(f"    会话数据恢复成功")
                        else:
                            logger.warning(f"    会话数据恢复失败，但新会话已创建")
                
                # 4. 清理过期会话
                try:
                    self.session_service.delete_session(session_id)
                    logger.info(f"    清理过期会话成功")
                except Exception as cleanup_error:
                    logger.warning(f"    清理过期会话失败: {cleanup_error}")
                
                logger.info(f"  会话恢复成功: {session_id} -> {new_session_id}")
                return {
                    'success': True,
                    'old_session_id': session_id,
                    'new_session_id': new_session_id,
                    'recovery_attempt': attempt + 1,
                    'data_recovered': bool(old_session_data)
                }
                
            except Exception as recovery_error:
                logger.error(f"  第 {attempt + 1} 次恢复失败: {type(recovery_error).__name__} - {recovery_error}")
                
                if attempt == config['max_recovery_attempts'] - 1:
                    logger.error(f"  会话恢复失败，已用完所有尝试次数")
                    return {
                        'success': False,
                        'error': recovery_error,
                        'attempts': attempt + 1,
                        'old_session_id': session_id,
                        'new_session_id': None
                    }
                
                # 短暂延迟后重试
                await asyncio.sleep(1.0)
        
        return {
            'success': False,
            'reason': 'max_attempts_exceeded',
            'old_session_id': session_id,
            'new_session_id': None
        }
    
    async def safe_resource_cleanup(self, 
                                   cleanup_func,
                                   resource_name: str,
                                   cleanup_args: tuple = (),
                                   cleanup_kwargs: dict = None) -> dict:
        """
        安全的资源清理，带异常处理
        
        Args:
            cleanup_func: 清理函数
            resource_name: 资源名称
            cleanup_args: 清理函数的位置参数
            cleanup_kwargs: 清理函数的关键字参数
            
        Returns:
            dict: 清理结果
        """
        from datetime import datetime
        
        cleanup_kwargs = cleanup_kwargs or {}
        config = self.cleanup_config
        
        logger.info(f"资源清理开始:")
        logger.info(f"  资源名称: {resource_name}")
        logger.info(f"  清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for attempt in range(config['cleanup_retry_count'] + 1):
            try:
                if attempt > 0:
                    logger.info(f"  第 {attempt + 1} 次清理尝试")
                
                # 设置清理超时
                cleanup_task = asyncio.create_task(
                    cleanup_func(*cleanup_args, **cleanup_kwargs)
                )
                
                try:
                    result = await asyncio.wait_for(cleanup_task, timeout=config['cleanup_timeout'])
                    logger.info(f"  资源清理成功: {resource_name}")
                    return {
                        'success': True,
                        'resource_name': resource_name,
                        'attempts': attempt + 1,
                        'result': result
                    }
                    
                except asyncio.TimeoutError:
                    logger.warning(f"  资源清理超时: {resource_name} (超时时间: {config['cleanup_timeout']}s)")
                    
                    if config['force_cleanup']:
                        # 强制取消清理任务
                        cleanup_task.cancel()
                        try:
                            await cleanup_task
                        except asyncio.CancelledError:
                            logger.info(f"    强制取消清理任务成功")
                        except Exception as cancel_error:
                            logger.warning(f"    取消清理任务异常: {cancel_error}")
                    
                    if attempt == config['cleanup_retry_count']:
                        logger.error(f"  资源清理超时，已用完所有重试次数: {resource_name}")
                        return {
                            'success': False,
                            'error': 'cleanup_timeout',
                            'resource_name': resource_name,
                            'attempts': attempt + 1
                        }
                    
                    # 短暂延迟后重试
                    await asyncio.sleep(0.5)
                    continue
                
            except Exception as cleanup_error:
                logger.error(f"  资源清理异常: {resource_name}")
                logger.error(f"    错误类型: {type(cleanup_error).__name__}")
                logger.error(f"    错误信息: {cleanup_error}")
                
                if attempt == config['cleanup_retry_count']:
                    logger.error(f"  资源清理失败，已用完所有重试次数: {resource_name}")
                    return {
                        'success': False,
                        'error': cleanup_error,
                        'resource_name': resource_name,
                        'attempts': attempt + 1
                    }
                
                # 短暂延迟后重试
                await asyncio.sleep(0.5)
        
        return {
            'success': False,
            'error': 'max_attempts_exceeded',
            'resource_name': resource_name,
            'attempts': config['cleanup_retry_count'] + 1
        }
    
    async def handle_api_error(self, 
                              error: Exception, 
                              request_id: str,
                              operation: str,
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理API错误的主入口
        
        Args:
            error: 异常对象
            request_id: 请求ID，用于跟踪重试
            operation: 操作类型（如'chat', 'upload', 'generate'）
            context: 错误上下文信息
            
        Returns:
            Dict[str, Any]: 错误处理结果
        """
        from datetime import datetime
        context = context or {}
        
        # 详细记录API错误信息
        logger.error(f"Dify API错误详情:")
        logger.error(f"  发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        logger.error(f"  请求ID: {request_id}")
        logger.error(f"  操作类型: {operation}")
        logger.error(f"  错误类型: {type(error).__name__}")
        logger.error(f"  错误信息: {str(error)}")
        
        # 记录上下文信息
        if context:
            logger.error(f"  上下文信息:")
            for key, value in context.items():
                # 避免记录敏感信息
                if key.lower() in ['password', 'token', 'api_key', 'secret']:
                    logger.error(f"    {key}: [已隐藏]")
                else:
                    logger.error(f"    {key}: {value}")
        
        # 记录重试历史
        retry_key = f"{operation}:{request_id}"
        current_retry_count = self.retry_count.get(retry_key, 0)
        logger.error(f"  重试信息: 当前重试次数 {current_retry_count}/{self.max_retries}")
        
        # 根据错误类型进行分类处理
        if isinstance(error, aiohttp.ClientResponseError):
            logger.error(f"  HTTP错误详情: 状态码 {error.status}, URL: {error.request_info.url if error.request_info else '未知'}")
            return await self._handle_http_error(error, request_id, operation, context)
        elif isinstance(error, asyncio.TimeoutError):
            logger.error(f"  超时错误: 请求超时")
            return await self._handle_timeout_error(error, request_id, operation, context)
        elif isinstance(error, aiohttp.ClientConnectionError):
            logger.error(f"  连接错误: {error}")
            return await self._handle_connection_error(error, request_id, operation, context)
        else:
            logger.error(f"  未知错误类型: {type(error).__name__}")
            return await self._handle_unknown_error(error, request_id, operation, context)
    
    async def _handle_http_error(self, 
                                error: aiohttp.ClientResponseError, 
                                request_id: str,
                                operation: str,
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理HTTP错误（4xx和5xx）
        
        Args:
            error: HTTP错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        status_code = error.status
        
        if status_code in self.client_errors:
            # 4xx客户端错误，不重试，返回具体错误信息
            return await self._handle_client_error(error, request_id, operation, context)
        elif status_code in self.server_errors:
            # 5xx服务器错误，尝试重试
            return await self._handle_server_error(error, request_id, operation, context)
        else:
            # 其他HTTP错误，降级处理
            return await self._fallback_to_mock(error, request_id, operation, context)
    
    async def _handle_client_error(self, 
                                  error: aiohttp.ClientResponseError, 
                                  request_id: str,
                                  operation: str,
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理4xx客户端错误
        
        Args:
            error: HTTP错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 错误处理结果
        """
        status_code = error.status
        
        # 特殊处理404 "Conversation Not Exists"错误
        if status_code == 404 and operation == 'chat':
            # 检查是否是对话不存在的错误
            error_text = str(error)
            if 'Conversation Not Exists' in error_text or 'conversation' in error_text.lower():
                logger.warning(f"检测到对话过期错误，将清除conversation_id并重新开始对话: {error_text}")
                return {
                    'success': False,
                    'error_type': 'conversation_expired',
                    'status_code': status_code,
                    'message': '对话已过期，将重新开始新对话',
                    'should_retry': True,  # 允许重试，但需要清除conversation_id
                    'clear_conversation_id': True,  # 标记需要清除conversation_id
                    'fallback_to_mock': False
                }
        
        # 其他客户端错误的正常处理
        error_message = self._get_client_error_message(status_code)
        
        logger.error(f"客户端错误: {status_code} - {error_message}, operation={operation}")
        
        return {
            'success': False,
            'error_type': 'client_error',
            'status_code': status_code,
            'message': error_message,
            'details': str(error),
            'should_retry': False,
            'fallback_to_mock': status_code in {401, 403}  # 认证/权限错误时降级
        }
    
    async def _handle_server_error(self, 
                                  error: aiohttp.ClientResponseError, 
                                  request_id: str,
                                  operation: str,
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理5xx服务器错误，实现重试机制
        
        Args:
            error: HTTP错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        retry_key = f"{operation}:{request_id}"
        current_retries = self.retry_count.get(retry_key, 0)
        
        if current_retries < self.max_retries:
            # 还可以重试
            self.retry_count[retry_key] = current_retries + 1
            delay = self._calculate_retry_delay(current_retries)
            
            logger.warning(f"服务器错误，准备重试: attempt={current_retries + 1}/{self.max_retries}, delay={delay}s")
            
            # 指数退避延迟
            await asyncio.sleep(delay)
            
            return {
                'success': False,
                'error_type': 'server_error',
                'status_code': error.status,
                'should_retry': True,
                'retry_attempt': current_retries + 1,
                'retry_delay': delay,
                'fallback_to_mock': False
            }
        else:
            # 重试次数用完，降级到Mock模式
            logger.error(f"服务器错误重试次数用完，降级到Mock模式: {error.status}")
            return await self._fallback_to_mock(error, request_id, operation, context)
    
    async def _handle_timeout_error(self, 
                                   error: asyncio.TimeoutError, 
                                   request_id: str,
                                   operation: str,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理超时错误
        
        Args:
            error: 超时错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        retry_key = f"{operation}:{request_id}"
        current_retries = self.retry_count.get(retry_key, 0)
        
        if current_retries < self.max_retries:
            # 超时错误可以重试
            self.retry_count[retry_key] = current_retries + 1
            delay = self._calculate_retry_delay(current_retries)
            
            logger.warning(f"请求超时，准备重试: attempt={current_retries + 1}/{self.max_retries}, delay={delay}s")
            
            await asyncio.sleep(delay)
            
            return {
                'success': False,
                'error_type': 'timeout_error',
                'should_retry': True,
                'retry_attempt': current_retries + 1,
                'retry_delay': delay,
                'fallback_to_mock': False
            }
        else:
            # 重试次数用完，降级到Mock模式
            logger.error("超时错误重试次数用完，降级到Mock模式")
            return await self._fallback_to_mock(error, request_id, operation, context)
    
    async def _handle_connection_error(self, 
                                      error: aiohttp.ClientConnectionError, 
                                      request_id: str,
                                      operation: str,
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理连接错误
        
        Args:
            error: 连接错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 连接错误通常表示网络问题，立即降级到Mock模式
        logger.error(f"连接错误，立即降级到Mock模式: {str(error)}")
        return await self._fallback_to_mock(error, request_id, operation, context)
    
    async def _handle_unknown_error(self, 
                                   error: Exception, 
                                   request_id: str,
                                   operation: str,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理未知错误
        
        Args:
            error: 未知错误对象
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.error(f"未知错误，降级到Mock模式: {type(error).__name__} - {str(error)}")
        return await self._fallback_to_mock(error, request_id, operation, context)
    
    async def _fallback_to_mock(self, 
                               error: Exception, 
                               request_id: str,
                               operation: str,
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """
        降级到Mock模式
        
        Args:
            error: 原始错误
            request_id: 请求ID
            operation: 操作类型
            context: 错误上下文
            
        Returns:
            Dict[str, Any]: 降级处理结果
        """
        # 切换到Mock模式
        fallback_reason = f"Error in {operation}: {type(error).__name__} - {str(error)}"
        self.mode_selector.switch_to_mock(fallback_reason)
        
        # 清理该请求的重试计数
        retry_key = f"{operation}:{request_id}"
        if retry_key in self.retry_count:
            del self.retry_count[retry_key]
        
        return {
            'success': True,  # 降级成功
            'error_type': 'fallback',
            'fallback_to_mock': True,
            'fallback_reason': fallback_reason,
            'original_error': str(error),
            'message': '服务暂时不可用，已切换到备用模式'
        }
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间（指数退避算法）
        
        Args:
            attempt: 当前重试次数（从0开始）
            
        Returns:
            float: 延迟时间（秒）
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        # 添加随机抖动，避免雷群效应
        jitter = random.uniform(0.1, 0.3) * delay
        final_delay = min(delay + jitter, self.max_delay)
        return final_delay
    
    def _get_client_error_message(self, status_code: int) -> str:
        """
        获取客户端错误的用户友好消息
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            str: 用户友好的错误消息
        """
        error_messages = {
            400: "请求参数有误，请检查输入内容",
            401: "身份验证失败，请检查API密钥配置",
            403: "访问权限不足，请联系管理员",
            404: "请求的资源不存在",
            413: "上传的文件过大，请减小文件大小后重试",
            422: "请求数据格式错误，请检查输入格式"
        }
        return error_messages.get(status_code, f"客户端请求错误: {status_code}")
    
    def reset_retry_count(self, request_id: str = None, operation: str = None):
        """
        重置重试计数
        
        Args:
            request_id: 请求ID，如果为None则重置所有
            operation: 操作类型，如果为None则重置所有
        """
        if request_id and operation:
            retry_key = f"{operation}:{request_id}"
            if retry_key in self.retry_count:
                del self.retry_count[retry_key]
                logger.debug(f"重置重试计数: {retry_key}")
        else:
            # 重置所有重试计数
            self.retry_count.clear()
            logger.info("重置所有重试计数")
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """
        获取重试统计信息
        
        Returns:
            Dict[str, Any]: 重试统计
        """
        return {
            'active_retries': len(self.retry_count),
            'retry_details': dict(self.retry_count),
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay
        }


class CircuitBreaker:
    """熔断器模式实现 - 防止级联故障"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, success_threshold: int = 3):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值，超过此值将打开熔断器
            timeout: 熔断器打开后的超时时间（秒）
            success_threshold: 半开状态下成功次数阈值，达到后关闭熔断器
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        logger.info(f"CircuitBreaker初始化: failure_threshold={failure_threshold}, timeout={timeout}s")
    
    async def call(self, func, *args, **kwargs):
        """
        通过熔断器执行函数调用
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            CircuitBreakerOpenError: 熔断器处于打开状态
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.success_count = 0
                logger.info("熔断器状态变更: OPEN -> HALF_OPEN")
            else:
                raise CircuitBreakerOpenError("熔断器处于打开状态，请求被拒绝")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """
        检查是否应该尝试重置熔断器
        
        Returns:
            bool: 是否应该重置
        """
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time > self.timeout
    
    def _on_success(self):
        """处理成功调用"""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
                logger.info("熔断器状态变更: HALF_OPEN -> CLOSED")
        elif self.state == "CLOSED":
            self.failure_count = 0
    
    def _on_failure(self):
        """处理失败调用"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.warning("熔断器状态变更: HALF_OPEN -> OPEN")
        elif self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"熔断器状态变更: CLOSED -> OPEN (失败次数: {self.failure_count})")
    
    def get_state(self) -> Dict[str, Any]:
        """
        获取熔断器状态
        
        Returns:
            Dict[str, Any]: 熔断器状态信息
        """
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'failure_threshold': self.failure_threshold,
            'success_threshold': self.success_threshold,
            'timeout': self.timeout,
            'last_failure_time': self.last_failure_time
        }
    
    def reset(self):
        """手动重置熔断器"""
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("熔断器已手动重置")


class CircuitBreakerOpenError(Exception):
    """熔断器打开状态异常"""
    pass


class AIService:
    """AI服务 - 支持Dify Agent集成和Mock模式"""
    
    def __init__(self, config: Dict[str, Any], redis_client=None):
        """
        初始化AI服务
        
        Args:
            config: AI服务配置
            redis_client: Redis客户端
        """
        self.config = config
        self.mode_selector = ModeSelector(config)
        self.session_manager = ConversationSessionManager(redis_client)
        
        # 初始化错误处理器和熔断器
        self.error_handler = DifyErrorHandler(self.mode_selector)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get('circuit_breaker_failure_threshold', 5),
            timeout=config.get('circuit_breaker_timeout', 60),
            success_threshold=config.get('circuit_breaker_success_threshold', 3)
        )
        
        # 保持向后兼容的属性
        self.dify_url = config.get('dify_url', '')
        self.dify_token = config.get('dify_token', '')
        self.mock_mode = config.get('mock_mode', True)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        
        # 测试数据配置
        self.test_data_config = config.get('test_data_config', {
            'default_test_case': """
测试场景：用户登录功能测试
测试目标：验证用户能够成功登录系统
前置条件：用户已注册账号
测试步骤：
1. 打开登录页面
2. 输入用户名和密码
3. 点击登录按钮
预期结果：成功跳转到用户仪表板页面
            """.strip()
        })
        
        logger.info(f"AI服务初始化完成，当前模式: {self.mode_selector.current_mode}")
        logger.info(f"错误处理器已启用，熔断器配置: failure_threshold={self.circuit_breaker.failure_threshold}")
    
    def get_error_handler(self) -> DifyErrorHandler:
        """获取错误处理器"""
        return self.error_handler
    
    def get_circuit_breaker(self) -> CircuitBreaker:
        """获取熔断器"""
        return self.circuit_breaker
    
    async def _execute_with_error_handling(self, 
                                          operation: str, 
                                          func, 
                                          *args, 
                                          **kwargs) -> Any:
        """
        使用错误处理和熔断器执行操作
        
        Args:
            operation: 操作名称
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        request_id = f"{operation}_{uuid.uuid4().hex[:8]}"
        max_attempts = self.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                # 通过熔断器执行操作
                result = await self.circuit_breaker.call(func, *args, **kwargs)
                
                # 成功时重置该操作的重试计数
                self.error_handler.reset_retry_count(request_id, operation)
                return result
                
            except CircuitBreakerOpenError as e:
                logger.warning(f"熔断器阻止操作: {operation}")
                # 熔断器打开时直接降级
                fallback_result = await self.error_handler._fallback_to_mock(
                    e, request_id, operation, {}
                )
                if fallback_result.get('fallback_to_mock'):
                    return await self._execute_fallback_operation(operation, *args, **kwargs)
                raise
                
            except Exception as e:
                # 使用错误处理器处理异常
                error_result = await self.error_handler.handle_api_error(
                    e, request_id, operation, {}
                )
                
                if error_result.get('should_retry') and attempt < max_attempts - 1:
                    # 需要重试且还有重试机会
                    logger.info(f"重试操作: {operation}, attempt={attempt + 1}")
                    continue
                elif error_result.get('fallback_to_mock'):
                    # 需要降级到Mock模式
                    logger.info(f"降级执行操作: {operation}")
                    return await self._execute_fallback_operation(operation, *args, **kwargs)
                else:
                    # 不能重试也不能降级，抛出异常
                    raise
        
        # 所有重试都失败了
        raise Exception(f"操作 {operation} 在 {max_attempts} 次尝试后仍然失败")
    
    async def _execute_fallback_operation(self, operation: str, *args, **kwargs) -> Any:
        """
        执行降级操作（Mock模式）
        
        Args:
            operation: 操作名称
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: Mock操作结果
        """
        # 确保切换到Mock模式
        if not self.mode_selector.is_mock_mode():
            self.mode_selector.switch_to_mock(f"Fallback for operation: {operation}")
        
        # 根据操作类型执行相应的Mock操作
        if operation == 'chat':
            mock_response = self._mock_chat_response(args[1] if len(args) > 1 else "", kwargs.get('context', {}))
            # 确保Mock响应包含success字段
            if 'success' not in mock_response:
                mock_response['success'] = True
            return mock_response
        elif operation == 'analyze_files':
            mock_response = self._mock_file_analysis(args[0] if len(args) > 0 else {})
            # 确保Mock响应包含success字段
            if 'success' not in mock_response:
                mock_response['success'] = True
            return mock_response
        elif operation == 'generate_test_cases':
            # 返回Mock生成器
            return self._mock_generation_stream_async(kwargs.get('context', {}))
        else:
            logger.warning(f"未知的降级操作: {operation}")
            return {'success': False, 'error': f'Unknown fallback operation: {operation}'}
    
    async def create_conversation_session(self, user_id: str) -> str:
        """
        创建新的对话会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 会话ID
        """
        return await self.session_manager.create_session(user_id)
    
    async def get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取对话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        return await self.session_manager.get_conversation_context(session_id)
    
    def analyze_files(self, files_info: Dict[str, Any], skip_dify_call: bool = False) -> Dict[str, Any]:
        """
        分析上传的文件 - 增强错误处理
        
        Args:
            files_info: 文件信息字典
            skip_dify_call: 是否跳过Dify调用（避免重复调用）
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 如果要求跳过Dify调用，直接返回本地分析结果
            if skip_dify_call:
                logger.info("跳过Dify调用，返回本地文件分析结果")
                return self._local_file_analysis(files_info)
            
            handler = self.mode_selector.get_handler()
            
            if self.mode_selector.is_mock_mode():
                return self._mock_file_analysis(files_info)
            else:
                # 使用同步方式调用Dify分析（保持向后兼容）
                return self._dify_analyze_files(files_info, handler)
                
        except Exception as e:
            logger.error(f"文件分析失败: {e}")
            # 使用错误处理器处理异常并降级到Mock模式
            request_id = f"analyze_{uuid.uuid4().hex[:8]}"
            
            # 同步调用错误处理器（简化版）
            self.mode_selector.switch_to_mock(f"文件分析异常: {str(e)}")
            return self._mock_file_analysis(files_info)
    
    async def analyze_files_async(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步分析上传的文件 - 完整错误处理支持
        
        Args:
            files_info: 文件信息字典
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        async def _analyze_operation():
            handler = self.mode_selector.get_handler()
            if isinstance(handler, DifyHandler):
                return await self._dify_analyze_files_async(files_info, handler)
            else:
                return self._mock_file_analysis(files_info)
        
        return await self._execute_with_error_handling('analyze_files', _analyze_operation)
    
    async def chat_with_agent(self, session_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        与AI Agent进行对话 - 支持会话管理和增强错误处理
        
        Args:
            session_id: 会话ID
            message: 用户消息
            context: 对话上下文（包含dify_conversation_id用于多轮对话）
            
        Returns:
            Dict[str, Any]: AI回复
        """
        try:
            # 获取或创建会话
            session = await self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"会话不存在，创建新会话: session_id={session_id}")
                await self.session_manager.create_session(session_id.split('_')[-1])  # 从session_id提取user_id
                session = await self.session_manager.get_session(session_id)
            
            # 添加用户消息到会话历史
            user_message = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            await self.session_manager.add_message(session_id, user_message)
            
            # 获取对话历史作为上下文
            conversation_history = await self.session_manager.get_conversation_context(session_id)
            enhanced_context = {
                **context,
                'chat_history': conversation_history,
                'session_id': session_id
            }
            
            handler = self.mode_selector.get_handler()
            
            if self.mode_selector.is_mock_mode():
                logger.warning("当前处于Mock模式，返回Mock响应")
                response = self._mock_chat_response(message, enhanced_context)
            else:
                # 优先从context获取dify_conversation_id（由ChatService从SessionService传入）
                dify_conversation_id = context.get('dify_conversation_id')
                
                # 如果context中没有，再从内部session_manager获取（兼容旧逻辑）
                if not dify_conversation_id:
                    dify_conversation_id = await self.session_manager.get_dify_conversation_id(session_id)
                
                # 获取保存的Dify系统参数
                from services.session_service import SessionService
                if hasattr(self, 'session_service') and isinstance(self.session_service, SessionService):
                    dify_system_params = self.session_service.get_dify_system_params(session_id)
                    enhanced_context['dify_system_params'] = dify_system_params
                
                logger.info(f"调用Dify API: session_id={session_id}, dify_conversation_id={dify_conversation_id}")
                
                try:
                    # 直接调用_dify_chat_request，不通过_execute_with_error_handling包装
                    # 这样可以正确处理conversation过期的情况
                    response = await self._dify_chat_request(session_id, dify_conversation_id, message, enhanced_context, handler)
                    
                    # 如果是首次对话且获得了新的conversation_id，保存到内部session_manager（兼容）
                    if not dify_conversation_id and response.get('conversation_id'):
                        await self.session_manager.update_conversation_id(session_id, response['conversation_id'])
                    
                    # 如果响应中包含系统参数，保存到SessionService
                    if response.get('dify_system_params') and hasattr(self, 'session_service'):
                        self.session_service.update_dify_system_params(session_id, response['dify_system_params'])
                    
                    logger.info(f"Dify API调用成功: session_id={session_id}, message_id={response.get('message_id', 'N/A')}")
                    
                except Exception as dify_error:
                    logger.error(f"Dify API调用失败: {dify_error}")
                    # 只有在明确的网络错误或服务不可用时才降级
                    error_str = str(dify_error).lower()
                    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable']):
                        logger.warning("检测到网络连接问题，降级到Mock模式")
                        self.mode_selector.switch_to_mock(f"网络连接异常: {str(dify_error)}")
                        response = self._mock_chat_response(message, enhanced_context)
                    else:
                        # 其他错误直接抛出，不降级
                        logger.error(f"Dify API调用异常，不降级: {dify_error}")
                        raise dify_error
            
            # 添加AI回复到会话历史
            ai_message = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                role="assistant",
                content=response.get('reply', ''),
                timestamp=datetime.utcnow(),
                metadata={
                    'message_id': response.get('message_id'),
                    'conversation_id': response.get('conversation_id')
                }
            )
            await self.session_manager.add_message(session_id, ai_message)
            
            return response
            
        except Exception as e:
            logger.error(f"AI对话异常: {e}")
            # 只有在网络连接问题时才降级到Mock模式
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable', 'ssl']):
                logger.warning(f"检测到网络连接问题，降级到Mock模式: {e}")
                self.mode_selector.switch_to_mock(f"网络连接异常: {str(e)}")
                mock_response = self._mock_chat_response(message, context)
                # 确保Mock响应包含success字段
                if 'success' not in mock_response:
                    mock_response['success'] = True
                return mock_response
            else:
                # 其他异常不降级，直接抛出
                logger.error(f"AI对话严重异常，不降级: {e}")
                raise e
    
    def _is_conversation_expired_error(self, error: Exception) -> bool:
        """
        检查是否是conversation过期错误
        
        Args:
            error: 异常对象
            
        Returns:
            bool: 是否是conversation过期错误
        """
        error_str = str(error).lower()
        return (
            'conversation not exists' in error_str or
            'conversation' in error_str and '404' in error_str or
            'not_found' in error_str and 'conversation' in error_str
        )
    
    async def send_message_streaming(self, session_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        发送流式消息 - 支持Server-Sent Events格式的流式响应
        
        Args:
            session_id: 会话ID
            message: 用户消息
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            # 获取会话信息
            session = await self.session_manager.get_session(session_id)
            if not session:
                logger.warning(f"会话不存在: session_id={session_id}")
                yield {
                    'event': 'error',
                    'error': 'session_not_found',
                    'message': '会话不存在或已过期'
                }
                return
            
            # 添加用户消息到会话历史
            user_message = ChatMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            await self.session_manager.add_message(session_id, user_message)
            
            # 获取对话上下文
            conversation_history = await self.session_manager.get_conversation_context(session_id)
            context = {
                'chat_history': conversation_history,
                'session_id': session_id
            }
            
            handler = self.mode_selector.get_handler()
            
            if self.mode_selector.is_mock_mode():
                logger.info(f"使用Mock模式处理流式消息: session_id={session_id}")
                async for chunk in self._mock_streaming_response(message, context):
                    yield chunk
            else:
                # 获取Dify conversation_id
                dify_conversation_id = await self.session_manager.get_dify_conversation_id(session_id)
                
                logger.info(f"使用Dify流式API: session_id={session_id}, conversation_id={dify_conversation_id}")
                
                try:
                    # 调用Dify流式API
                    async for chunk in self._dify_streaming_chat(session_id, dify_conversation_id, message, context, handler):
                        yield chunk
                        
                except Exception as dify_error:
                    logger.error(f"Dify流式API调用失败: {dify_error}")
                    # 降级到Mock模式
                    self.mode_selector.switch_to_mock(f"流式API异常: {str(dify_error)}")
                    async for chunk in self._mock_streaming_response(message, context):
                        yield chunk
                        
        except Exception as e:
            logger.error(f"流式消息发送异常: {e}")
            yield {
                'event': 'error',
                'error': 'internal_error',
                'message': str(e)
            }
    
    async def _mock_streaming_response(self, message: str, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Mock流式响应 - 模拟逐字输出效果
        
        Args:
            message: 用户消息
            context: 对话上下文
            
        Yields:
            Dict[str, Any]: 流式响应块
        """
        # 生成Mock回复内容
        mock_response = self._mock_chat_response(message, context)
        reply_content = mock_response.get('reply', '抱歉，我无法处理您的请求。')
        
        # 模拟流式输出，每次发送几个字符
        chunk_size = 3  # 每次发送3个字符
        
        for i in range(0, len(reply_content), chunk_size):
            chunk_content = reply_content[i:i + chunk_size]
            
            yield {
                'event': 'message',
                'content': chunk_content,
                'message_id': f"mock_msg_{uuid.uuid4().hex[:8]}",
                'conversation_id': mock_response.get('conversation_id', f"mock_conv_{uuid.uuid4().hex[:8]}")
            }
            
            # 添加延迟模拟真实的打字效果
            await asyncio.sleep(0.1)
        
        # 发送消息结束事件
        yield {
            'event': 'message_end',
            'message_id': f"mock_msg_{uuid.uuid4().hex[:8]}",
            'conversation_id': mock_response.get('conversation_id', f"mock_conv_{uuid.uuid4().hex[:8]}"),
            'metadata': {
                'usage': {'tokens': len(reply_content)},
                'mock_mode': True
            }
        }
    
    async def _dify_streaming_chat(self, session_id: str, conversation_id: str, message: str, context: Dict[str, Any], handler) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Dify流式聊天 - 调用Dify的流式API
        
        Args:
            session_id: 会话ID
            conversation_id: Dify对话ID
            message: 用户消息
            context: 对话上下文
            handler: Dify处理器
            
        Yields:
            Dict[str, Any]: 流式响应块
        """
        try:
            # 调用Dify的异步流式方法
            stream_response = await handler.send_message_async(
                conversation_id=conversation_id,
                message=message,
                context=context,
                stream=True
            )
            
            # 处理流式响应
            if hasattr(stream_response, '__aiter__'):
                async for chunk in stream_response:
                    if chunk:
                        yield chunk
                        
                        # 如果是消息结束事件，更新会话信息
                        if chunk.get('event') == 'message_end':
                            new_conversation_id = chunk.get('conversation_id')
                            if new_conversation_id and new_conversation_id != conversation_id:
                                await self.session_manager.update_conversation_id(session_id, new_conversation_id)
            else:
                # 如果不是流式响应，转换为流式格式
                content = stream_response.get('answer', '') if isinstance(stream_response, dict) else str(stream_response)
                
                # 分块发送
                chunk_size = 5
                for i in range(0, len(content), chunk_size):
                    chunk_content = content[i:i + chunk_size]
                    yield {
                        'event': 'message',
                        'content': chunk_content,
                        'message_id': stream_response.get('message_id', f"msg_{uuid.uuid4().hex[:8]}"),
                        'conversation_id': stream_response.get('conversation_id', conversation_id)
                    }
                    await asyncio.sleep(0.05)
                
                # 发送结束事件
                yield {
                    'event': 'message_end',
                    'message_id': stream_response.get('message_id', f"msg_{uuid.uuid4().hex[:8]}"),
                    'conversation_id': stream_response.get('conversation_id', conversation_id),
                    'metadata': stream_response.get('metadata', {})
                }
                
        except Exception as e:
            logger.error(f"Dify流式聊天异常: {e}")
            yield {
                'event': 'error',
                'error': 'dify_stream_error',
                'message': str(e)
            }

    async def generate_test_cases(self, session_id: str, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成测试用例 - 修复异步生成器问题
        
        Args:
            session_id: 会话ID
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        async def _generate_operation():
            # 获取会话信息
            session = await self.session_manager.get_session(session_id)
            if session:
                # 获取对话历史
                conversation_history = await self.session_manager.get_conversation_context(session_id)
                enhanced_context = {
                    **context,
                    'chat_history': conversation_history,
                    'session_id': session_id
                }
            else:
                enhanced_context = context
            
            handler = self.mode_selector.get_handler()
            
            if self.mode_selector.is_mock_mode():
                # 修复：直接返回异步生成器，不要包装
                async for data in self._mock_generation_stream_async(enhanced_context):
                    yield data
            else:
                dify_conversation_id = await self.session_manager.get_dify_conversation_id(session_id) if session else None
                # 修复：直接迭代异步生成器，不要await
                async for data in self._dify_generation_stream_async(session_id, dify_conversation_id, enhanced_context, handler):
                    yield data
        
        # 修复：直接迭代异步生成器
        try:
            async for data in _generate_operation():
                yield data
        except Exception as e:
            logger.error(f"测试用例生成失败: {e}")
            # 降级到Mock模式
            self.mode_selector.switch_to_mock(f"生成异常: {str(e)}")
            async for data in self._mock_generation_stream_async(context):
                yield data
    
    def _mock_file_analysis(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock文件分析 - 使用预设测试数据
        
        Args:
            files_info: 文件信息
            
        Returns:
            Dict[str, Any]: Mock分析结果
        """
        # 使用预设的测试用例描述
        test_case_description = self.test_data_config.get('default_test_case', '默认测试用例描述')
        
        analysis_result = {
            'success': True,  # 添加success字段
            'template_info': f'检测到模板文件包含 {random.randint(15, 30)} 个测试场景，主要涉及用户管理、权限控制和数据操作功能。',
            'history_info': f'发现 {random.randint(40, 80)} 条历史用例可供参考，覆盖了登录、搜索、订单等核心业务流程。',
            'suggestions': [
                "建议增加异常场景的测试覆盖",
                "推荐添加性能测试用例",
                "考虑增加边界值测试"
            ],
            'extracted_content': test_case_description,
            'test_scenario': 'login'  # 默认场景
        }
        
        # 分析模板文件
        if 'case_template' in files_info:
            template_file = files_info['case_template']
            analysis_result['template_info'] = f"检测到模板文件包含 {random.randint(15, 30)} 个测试场景，主要涉及用户管理、权限控制和数据操作功能。"
        
        # 分析历史用例文件
        if 'history_case' in files_info:
            history_file = files_info['history_case']
            analysis_result['history_info'] = f"发现 {random.randint(40, 80)} 条历史用例可供参考，覆盖了登录、搜索、订单等核心业务流程。"
        
        # 分析AW模板文件
        if 'aw_template' in files_info:
            aw_file = files_info['aw_template']
            analysis_result['suggestions'].append("检测到AW工程模板，建议重点关注接口兼容性测试。")
        
        logger.info(f"Mock文件分析完成: {len(files_info)} 个文件，使用测试数据")
        logger.debug(f"使用的测试用例描述: {test_case_description[:100]}...")
        
        return analysis_result
    
    def _local_file_analysis(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        本地文件分析 - 不调用Dify，只进行本地分析
        
        Args:
            files_info: 文件信息
            
        Returns:
            Dict[str, Any]: 本地分析结果
        """
        logger.info("执行本地文件分析，不调用Dify API")
        
        analysis_result = {
            'success': True,
            'template_info': '文件上传成功，已准备进行自动分析',
            'history_info': '',
            'suggestions': ['系统将自动分析文件内容并开始对话'],
            'local_analysis': True  # 标记这是本地分析
        }
        
        # 分析模板文件
        if 'case_template' in files_info:
            template_file = files_info['case_template']
            file_size = template_file.get('file_size', 0)
            analysis_result['template_info'] = f"检测到测试用例文件 ({file_size} 字节)，准备进行自动解析和分析"
        
        # 分析历史用例文件
        if 'history_case' in files_info:
            history_file = files_info['history_case']
            analysis_result['history_info'] = "检测到历史用例文件，将作为参考"
        
        # 分析AW模板文件
        if 'aw_template' in files_info:
            aw_file = files_info['aw_template']
            analysis_result['suggestions'].append("检测到AW工程模板文件")
        
        logger.info(f"本地文件分析完成: {len(files_info)} 个文件")
        return analysis_result
    
    def _mock_chat_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock对话响应
        
        Args:
            message: 用户消息
            context: 对话上下文
            
        Returns:
            Dict[str, Any]: Mock回复
        """
        # 检查是否是开始生成的关键词
        if "开始生成" in message.lower() or "start" in message.lower():
            return {
                'success': True,  # 添加success字段
                'reply': "好的，我现在开始为您生成测试用例。请稍等...",
                'need_more_info': False,
                'ready_to_generate': True
            }
        
        # 获取对话历史长度来决定回复
        chat_history = context.get('chat_history', [])
        
        # 为自动分析提供特殊的Mock回复
        if context.get('user_initiated') and '测试用例内容' in message:
            return {
                'success': True,  # 添加success字段
                'reply': f"我已经分析了您上传的测试用例文件。这个用例包含了基本的测试流程。为了生成更完整的测试用例，我想了解：\n\n1. 这个系统主要的用户群体是谁？\n2. 是否有特殊的安全性要求？\n3. 有什么特殊的业务规则需要考虑吗？",
                'need_more_info': True,
                'ready_to_generate': False,
                'conversation_id': str(uuid.uuid4()),  # 使用标准UUID格式
                'suggestions': [
                    "描述系统的用户类型和权限",
                    "说明安全性和合规性要求",
                    "提供业务规则和约束条件"
                ]
            }
        
        # 默认Mock回复
        mock_responses = [
            "好的，我已经分析了您上传的文件。请描述一下您希望生成的测试用例类型和测试场景。",
            "了解了您的需求。关于登录功能测试，您希望覆盖哪些场景：1.正常登录 2.密码错误 3.账号不存在 4.验证码校验？",
            "很好！我还需要了解一些细节：您希望测试哪些浏览器兼容性？是否需要包含移动端测试？",
            "明白了。最后确认一下测试数据：您希望使用真实的测试账号还是模拟数据？如果准备好了，请回复'开始生成'。",
            "收到！我现在有足够的信息来生成高质量的测试用例了。请告诉我是否可以开始生成？"
        ]
        
        response_index = len([msg for msg in chat_history if msg.get('role') == 'user']) % len(mock_responses)
        
        # 模拟思考时间
        time.sleep(random.uniform(0.5, 1.5))
        
        return {
            'success': True,  # 添加success字段
            'reply': mock_responses[response_index],
            'need_more_info': True,
            'ready_to_generate': False,
            'suggestions': [
                "您可以描述具体的测试场景",
                "告诉我需要重点关注的功能模块",
                "说明测试的优先级要求"
            ]
        }
    
    def _mock_generation_stream(self, context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Mock生成流式响应
        
        Args:
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        # 模拟生成过程的各个阶段
        stages = [
            {"stage": "analyzing", "message": "正在分析需求和文件内容...", "progress": 10},
            {"stage": "planning", "message": "正在规划测试用例结构...", "progress": 25},
            {"stage": "generating", "message": "正在生成测试步骤...", "progress": 50},
            {"stage": "optimizing", "message": "正在优化测试用例...", "progress": 75},
            {"stage": "formatting", "message": "正在格式化输出...", "progress": 90},
        ]
        
        for stage in stages:
            yield {
                'type': 'progress',
                'data': stage
            }
            time.sleep(random.uniform(1.0, 2.0))
        
        # 生成Mock测试用例数据
        test_cases = self._generate_mock_test_cases(context)
        
        yield {
            'type': 'complete',
            'data': {
                'test_cases': test_cases,
                'total_count': len(test_cases),
                'message': f"成功生成 {len(test_cases)} 条测试用例"
            }
        }
    
    def _generate_mock_test_cases(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成Mock测试用例数据
        
        Args:
            context: 生成上下文
            
        Returns:
            List[Dict[str, Any]]: Mock测试用例列表
        """
        test_cases = [
            {
                'id': 'TC001',
                'name': '用户登录功能测试',
                'preconditions': [
                    {
                        'id': 'pre1',
                        'name': '用户已注册账号',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec1',
                                'type': 'api',
                                'name': '接口调用 - 检查用户存在',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/users/check',
                                    'expected': True
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's1',
                        'name': '打开登录页面',
                        'expanded': True,
                        'components': [
                            {
                                'id': 'c1',
                                'type': 'api',
                                'name': '接口调用 - 获取登录页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/login'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's2',
                        'name': '输入用户名和密码',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c2',
                                'type': 'input',
                                'name': '输入用户名',
                                'params': {
                                    'selector': '#username',
                                    'value': 'testuser'
                                }
                            },
                            {
                                'id': 'c3',
                                'type': 'input',
                                'name': '输入密码',
                                'params': {
                                    'selector': '#password',
                                    'value': 'password123'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's3',
                        'name': '点击登录按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c4',
                                'type': 'button',
                                'name': '点击登录',
                                'params': {
                                    'selector': '#login-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp1',
                        'name': '成功跳转到用户仪表板页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc1',
                                'type': 'assert',
                                'name': '断言 - URL正确',
                                'params': {
                                    'type': 'equals',
                                    'expected': '/dashboard'
                                }
                            },
                            {
                                'id': 'expc2',
                                'type': 'assert',
                                'name': '断言 - 显示用户信息',
                                'params': {
                                    'type': 'exists',
                                    'expected': '.user-info'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'TC002',
                'name': '用户登录失败测试',
                'preconditions': [
                    {
                        'id': 'pre2',
                        'name': '用户账号存在但密码错误',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec2',
                                'type': 'api',
                                'name': '接口调用 - 验证用户存在',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/users/testuser',
                                    'expected': True
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's4',
                        'name': '打开登录页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c5',
                                'type': 'api',
                                'name': '接口调用 - 获取登录页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/login'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's5',
                        'name': '输入错误密码',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c6',
                                'type': 'input',
                                'name': '输入用户名',
                                'params': {
                                    'selector': '#username',
                                    'value': 'testuser'
                                }
                            },
                            {
                                'id': 'c7',
                                'type': 'input',
                                'name': '输入错误密码',
                                'params': {
                                    'selector': '#password',
                                    'value': 'wrongpassword'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's6',
                        'name': '点击登录按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c8',
                                'type': 'button',
                                'name': '点击登录',
                                'params': {
                                    'selector': '#login-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp2',
                        'name': '显示密码错误提示',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc3',
                                'type': 'assert',
                                'name': '断言 - 错误信息显示',
                                'params': {
                                    'type': 'contains',
                                    'expected': '密码错误'
                                }
                            },
                            {
                                'id': 'expc4',
                                'type': 'assert',
                                'name': '断言 - 仍在登录页面',
                                'params': {
                                    'type': 'equals',
                                    'expected': '/login'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'TC003',
                'name': '搜索功能测试',
                'preconditions': [
                    {
                        'id': 'pre3',
                        'name': '用户已登录系统',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec3',
                                'type': 'api',
                                'name': '接口调用 - 验证登录状态',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/auth/status',
                                    'expected': 'authenticated'
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's7',
                        'name': '打开搜索页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c9',
                                'type': 'api',
                                'name': '接口调用 - 获取搜索页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/search'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's8',
                        'name': '输入搜索关键词',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c10',
                                'type': 'input',
                                'name': '输入搜索词',
                                'params': {
                                    'selector': '#search-input',
                                    'value': '测试关键词'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's9',
                        'name': '点击搜索按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c11',
                                'type': 'button',
                                'name': '点击搜索',
                                'params': {
                                    'selector': '#search-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp3',
                        'name': '显示搜索结果',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc5',
                                'type': 'assert',
                                'name': '断言 - 结果列表存在',
                                'params': {
                                    'type': 'exists',
                                    'expected': '.search-results'
                                }
                            },
                            {
                                'id': 'expc6',
                                'type': 'assert',
                                'name': '断言 - 结果数量大于0',
                                'params': {
                                    'type': 'greater_than',
                                    'expected': 0
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        return test_cases
    
    def _dify_analyze_files(self, files_info: Dict[str, Any], handler: DifyHandler) -> Dict[str, Any]:
        """
        使用Dify分析文件 - 修改为使用异步调用以支持代理
        
        Args:
            files_info: 文件信息
            handler: Dify处理器
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 使用预设的测试用例描述作为初始输入
            test_case_description = self.test_data_config.get('default_test_case', '默认测试用例描述')
            
            # 构建分析上下文
            context = {
                'files_info': files_info,
                'test_case_description': test_case_description,
                'analysis_type': 'file_analysis'
            }
            
            # 使用异步调用但在同步上下文中运行
            import asyncio
            
            async def _async_analyze():
                return await handler.send_message_async(
                    conversation_id=None,
                    message=f"请分析以下文件信息并提取测试用例描述：{test_case_description}",
                    context=context,
                    stream=False
                )
            
            # 在同步上下文中运行异步函数
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_analyze())
                        response = future.result()
                else:
                    response = loop.run_until_complete(_async_analyze())
            except RuntimeError:
                # 没有事件循环，创建新的
                response = asyncio.run(_async_analyze())
            
            return self._parse_dify_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Dify文件分析异常: {e}")
            raise
    
    async def _dify_chat_request(self, session_id: str, conversation_id: Optional[str], message: str, context: Dict[str, Any], handler: DifyHandler) -> Dict[str, Any]:
        """
        使用Dify进行对话
        
        Args:
            session_id: 会话ID
            conversation_id: Dify对话ID
            message: 用户消息
            context: 对话上下文
            handler: Dify处理器
            
        Returns:
            Dict[str, Any]: 对话回复
        """
        try:
            response = await handler.send_message_async(
                conversation_id=conversation_id,
                message=message,
                context=context,
                stream=False
            )
            
            parsed_response = self._parse_dify_chat_response(response)
            
            # 添加conversation_id到响应中
            if response.get('conversation_id'):
                parsed_response['conversation_id'] = response['conversation_id']
            if response.get('message_id'):
                parsed_response['message_id'] = response['message_id']
            
            return parsed_response
            
        except Exception as e:
            # 检查是否是conversation过期错误
            if self._is_conversation_expired_error(e) and conversation_id:
                logger.warning(f"检测到conversation过期，返回特殊标记: {conversation_id}")
                # 返回特殊响应，标记conversation过期
                return {
                    'reply': '对话已过期，正在重新开始新对话...',
                    'conversation_expired': True,
                    'expired_conversation_id': conversation_id
                }
            else:
                logger.error(f"Dify对话异常: {e}")
                raise
    
    def _dify_generation_stream(self, session_id: str, context: Dict[str, Any], handler: DifyHandler) -> Generator[Dict[str, Any], None, None]:
        """
        使用Dify进行流式生成 (同步版本，已废弃，建议使用异步版本)
        
        Args:
            session_id: 会话ID
            context: 生成上下文
            handler: Dify处理器
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            # 构建生成请求消息
            generation_message = "请根据之前的对话内容生成详细的测试用例"
            
            request_data = {
                'inputs': {
                    'sys.query': generation_message,
                    'context': json.dumps(context)
                },
                'query': generation_message,
                'response_mode': 'streaming',
                'conversation_id': session_id,
                'user': f'user_{session_id}'
            }
            
            response = handler.session.post(
                f'{handler.base_url}/chat-messages',
                json=request_data,
                timeout=handler.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # 收集所有SSE数据
                sse_lines = []
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        sse_lines.append(line_str)
                
                # 使用StreamProcessor处理SSE数据
                sse_text = '\n'.join(sse_lines)
                
                # 由于这是同步方法，我们需要运行异步处理器
                import asyncio
                
                async def process_sse():
                    async for result in handler.stream_processor.process_stream_text(sse_text):
                        yield result
                
                # 运行异步生成器并转换为同步
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async_gen = process_sse()
                    while True:
                        try:
                            result = loop.run_until_complete(async_gen.__anext__())
                            yield result
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()
                    
            else:
                logger.error(f"Dify流式生成请求失败: {response.status_code}")
                raise Exception(f"Dify API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Dify流式生成异常: {e}")
            raise
    
    def _parse_dify_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Dify文件分析响应
        
        Args:
            response: Dify响应数据
            
        Returns:
            Dict[str, Any]: 解析后的分析结果
        """
        try:
            answer = response.get('answer', '')
            # 这里需要根据实际的Dify响应格式进行解析
            # 假设Dify返回JSON格式的分析结果
            try:
                analysis_result = json.loads(answer)
            except json.JSONDecodeError:
                # 如果不是JSON格式，创建默认结构
                analysis_result = {
                    'template_info': answer if answer else '文件分析完成',
                    'history_info': '',
                    'suggestions': ['请描述您的测试需求']
                }
            
            # 确保包含success字段
            if 'success' not in analysis_result:
                analysis_result['success'] = True
                
            return analysis_result
        except Exception as e:
            logger.error(f"解析Dify分析响应失败: {e}")
            # 返回默认结构，包含success字段
            return {
                'success': True,
                'template_info': '文件分析完成',
                'history_info': '',
                'suggestions': ['请描述您的测试需求']
            }
    
    def _parse_dify_chat_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Dify对话响应
        
        Args:
            response: Dify响应数据
            
        Returns:
            Dict[str, Any]: 解析后的对话回复
        """
        try:
            answer = response.get('answer', '')
            
            # 检查是否准备生成
            ready_to_generate = "开始生成" in answer or "ready to generate" in answer.lower()
            
            # 提取系统参数（用于后续请求）
            dify_system_params = {}
            metadata = response.get('metadata', {})
            
            # 从metadata中提取系统参数
            if metadata:
                # 提取可能的系统参数
                for key in ['user_id', 'app_id', 'workflow_id', 'workflow_run_id', 'files', 'query', 'conversation_id', 'dialogue_count']:
                    if key in metadata:
                        dify_system_params[f'sys.{key}'] = metadata[key]
            
            # 从响应的顶级字段中提取系统参数
            for key in ['conversation_id', 'message_id']:
                if key in response:
                    dify_system_params[f'sys.{key}'] = response[key]
            
            # 如果响应中直接包含sys开头的字段，也提取出来
            for key, value in response.items():
                if key.startswith('sys.'):
                    dify_system_params[key] = value
            
            result = {
                'success': True,  # 添加success字段
                'reply': answer,
                'need_more_info': not ready_to_generate,
                'ready_to_generate': ready_to_generate,
                'suggestions': []
            }
            
            # 如果有系统参数，添加到结果中
            if dify_system_params:
                result['dify_system_params'] = dify_system_params
                logger.debug(f"提取到Dify系统参数: {dify_system_params}")
            
            return result
            
        except Exception as e:
            logger.error(f"解析Dify对话响应失败: {e}")
            return {
                'success': False,  # 添加success字段
                'reply': '抱歉，我遇到了一些问题，请重试。',
                'need_more_info': True,
                'ready_to_generate': False
            }
    
    async def _mock_generation_stream_async(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Mock生成流式响应 - 异步版本
        
        Args:
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        import asyncio
        
        # 模拟生成过程的各个阶段
        stages = [
            {"stage": "analyzing", "message": "正在分析需求和文件内容...", "progress": 10},
            {"stage": "planning", "message": "正在规划测试用例结构...", "progress": 25},
            {"stage": "generating", "message": "正在生成测试步骤...", "progress": 50},
            {"stage": "optimizing", "message": "正在优化测试用例...", "progress": 75},
            {"stage": "formatting", "message": "正在格式化输出...", "progress": 90},
        ]
        
        for stage in stages:
            yield {
                'type': 'progress',
                'data': stage
            }
            # 使用asyncio.sleep()替代time.sleep()，模拟真实的生成时间
            await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # 生成Mock测试用例数据
        test_cases = self._generate_mock_test_cases(context)
        
        # 确保返回正确的数据结构，与真实Dify响应一致
        yield {
            'type': 'complete',
            'data': {
                'test_cases': test_cases,
                'total_count': len(test_cases),
                'message': f"成功生成 {len(test_cases)} 条测试用例"
            }
        }
        
        logger.info(f"Mock模式生成完成，共生成 {len(test_cases)} 条测试用例")
    
    async def _dify_generation_stream_async(self, session_id: str, conversation_id: Optional[str], context: Dict[str, Any], handler: DifyHandler) -> AsyncGenerator[Dict[str, Any], None]:
        """
        使用Dify进行流式生成 (异步版本)
        
        Args:
            session_id: 会话ID
            conversation_id: Dify对话ID
            context: 生成上下文
            handler: Dify处理器
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            # 构建生成请求消息
            generation_message = "请根据之前的对话内容生成详细的测试用例"
            
            # 使用异步方法发送流式请求
            stream_response = await handler.send_message_async(
                conversation_id=conversation_id,
                message=generation_message,
                context=context,
                stream=True
            )
            
            # 处理流式响应 - StreamProcessor已经在DifyHandler中处理了
            async for data in stream_response:
                yield data
                    
        except Exception as e:
            logger.error(f"Dify异步流式生成异常: {e}")
            yield {
                'type': 'error',
                'data': {
                    'message': f'生成失败: {str(e)}'
                }
            }
    
    
    async def cleanup_session(self, session_id: str):
        """
        清理会话资源
        
        Args:
            session_id: 会话ID
        """
        try:
            # 完成会话
            await self.complete_session(session_id)
            
            # 如果使用Dify模式，清理相关资源
            if not self.mode_selector.is_mock_mode():
                handler = self.mode_selector.get_handler()
                if hasattr(handler, 'close'):
                    await handler.close()
            
            logger.info(f"会话清理完成: session_id={session_id}")
            
        except Exception as e:
            logger.error(f"会话清理失败: session_id={session_id}, error={e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        health_status = {
            'status': 'healthy',
            'mode': self.mode_selector.current_mode,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.mode_selector.is_mock_mode():
            health_status.update({
                'message': 'Mock模式运行正常',
                'dify_connection': 'not_used'
            })
            logger.info("健康检查完成 - Mock模式")
        else:
            # Dify模式，检查连接状态
            handler = self.mode_selector.get_handler()
            if isinstance(handler, DifyHandler):
                try:
                    connection_ok = handler.test_connection()
                    health_status.update({
                        'message': 'Dify模式运行正常' if connection_ok else 'Dify连接异常',
                        'dify_connection': 'connected' if connection_ok else 'disconnected'
                    })
                    
                    if not connection_ok:
                        health_status['status'] = 'degraded'
                        
                except Exception as e:
                    health_status.update({
                        'status': 'unhealthy',
                        'message': f'Dify连接检查失败: {str(e)}',
                        'dify_connection': 'error'
                    })
            
            # 添加错误处理器和熔断器状态
            health_status.update({
                'error_handler': self.error_handler.get_retry_stats(),
                'circuit_breaker': self.circuit_breaker.get_state()
            })
            
            logger.info(f"健康检查完成 - Dify模式: {health_status['dify_connection']}")
        
        return health_status
    
    async def _dify_analyze_files_async(self, files_info: Dict[str, Any], handler: DifyHandler) -> Dict[str, Any]:
        """
        使用Dify异步分析文件
        
        Args:
            files_info: 文件信息
            handler: Dify处理器
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 使用预设的测试用例描述作为初始输入
            test_case_description = self.test_data_config.get('default_test_case', '默认测试用例描述')
            
            # 构建分析上下文
            context = {
                'files_info': files_info,
                'test_case_description': test_case_description,
                'analysis_type': 'file_analysis'
            }
            
            # 发送异步分析请求到Dify
            response = await handler.send_message_async(
                conversation_id=None,
                message=f"请分析以下文件信息并提取测试用例描述：{test_case_description}",
                context=context,
                stream=False
            )
            
            return self._parse_dify_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Dify异步文件分析异常: {e}")
            raise
    
    async def cleanup_all_resources(self):
        """
        清理所有资源 - 全局资源清理方法
        
        这个方法应该在应用关闭时调用，确保所有资源都被正确清理
        """
        try:
            logger.info("开始清理AIService所有资源")
            
            # 清理会话管理器中的过期会话
            if hasattr(self, 'session_manager') and self.session_manager:
                try:
                    await self.session_manager.cleanup_expired_sessions()
                    logger.debug("会话管理器清理完成")
                except Exception as e:
                    logger.warning(f"清理会话管理器失败: {e}")
            
            # 清理Dify处理器资源
            if not self.mode_selector.is_mock_mode():
                handler = self.mode_selector.get_handler()
                if hasattr(handler, 'close'):
                    try:
                        await handler.close()
                        logger.debug("Dify处理器清理完成")
                    except Exception as e:
                        logger.warning(f"清理Dify处理器失败: {e}")
            
            # 重置错误处理器状态
            if hasattr(self, 'error_handler') and self.error_handler:
                try:
                    self.error_handler.reset_retry_count()
                    logger.debug("错误处理器状态重置完成")
                except Exception as e:
                    logger.warning(f"重置错误处理器失败: {e}")
            
            # 重置熔断器状态
            if hasattr(self, 'circuit_breaker') and self.circuit_breaker:
                try:
                    self.circuit_breaker.reset()
                    logger.debug("熔断器状态重置完成")
                except Exception as e:
                    logger.warning(f"重置熔断器失败: {e}")
            
            logger.info("AIService资源清理完成")
            
        except Exception as e:
            logger.error(f"AIService资源清理异常: {e}")
            raise
    
    def __del__(self):
        """析构函数 - 确保资源清理"""
        try:
            # 在析构函数中只做简单的同步清理，避免复杂的异步操作
            
            # 清理模式选择器
            if hasattr(self, 'mode_selector') and self.mode_selector:
                try:
                    # 如果有同步的清理方法，可以调用
                    if hasattr(self.mode_selector, 'cleanup'):
                        self.mode_selector.cleanup()
                    logger.debug("析构函数中清理模式选择器成功")
                except Exception as e:
                    logger.warning(f"析构函数中清理模式选择器失败: {e}")
            
            # 清理错误处理器
            if hasattr(self, 'error_handler') and self.error_handler:
                try:
                    self.error_handler.retry_count.clear()
                    logger.debug("析构函数中清理错误处理器成功")
                except Exception as e:
                    logger.warning(f"析构函数中清理错误处理器失败: {e}")
                    
        except Exception as e:
            # 析构函数中不应该抛出异常
            try:
                logger.warning(f"AIService析构函数执行失败: {e}")
            except:
                # 如果连日志都无法记录，就静默忽略
                pass
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict[str, Any]: 服务统计
        """
        stats = {
            'mode': self.mode_selector.current_mode,
            'error_handler_stats': self.error_handler.get_retry_stats(),
            'circuit_breaker_state': self.circuit_breaker.get_state(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 如果是Dify模式，添加处理器统计
        if not self.mode_selector.is_mock_mode():
            handler = self.mode_selector.get_handler()
            if isinstance(handler, DifyHandler):
                stats['dify_workflows'] = handler.get_all_workflows()
        
        return stats
    
    def reset_error_handling(self):
        """重置错误处理状态"""
        self.error_handler.reset_retry_count()
        self.circuit_breaker.reset()
        logger.info("错误处理状态已重置")
    
    async def switch_mode(self, target_mode: str, reason: str = "manual"):
        """
        手动切换服务模式
        
        Args:
            target_mode: 目标模式 ('mock' 或 'dify')
            reason: 切换原因
        """
        if target_mode == 'mock':
            self.mode_selector.switch_to_mock(reason)
        elif target_mode == 'dify':
            if not self.config.get('mock_mode', True):
                self.mode_selector.switch_to_dify()
                # 重置错误处理状态
                self.reset_error_handling()
            else:
                logger.warning("配置中启用了Mock模式，无法切换到Dify模式")
        else:
            logger.error(f"未知的目标模式: {target_mode}")
        
        logger.info(f"服务模式已切换到: {self.mode_selector.current_mode}, 原因: {reason}")