import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from services.chat_service import ChatService
from services.ai_service import AIService
from services.session_service import SessionService


class TestChatService:
    """对话服务单元测试"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI服务"""
        ai_service = Mock(spec=AIService)
        ai_service.chat_with_agent.return_value = {
            'reply': '这是AI的回复',
            'need_more_info': True,
            'ready_to_generate': False,
            'suggestions': ['建议1', '建议2']
        }
        return ai_service
    
    @pytest.fixture
    def mock_session_service(self):
        """Mock 会话服务"""
        session_service = Mock(spec=SessionService)
        session_service.is_session_valid.return_value = True
        session_service.get_session_data.return_value = {
            'session_id': 'test_session_123',
            'status': 'chatting',
            'chat_history': [],
            'files': {},
            'config': {},
            'analysis_result': {}
        }
        return session_service
    
    @pytest.fixture
    def chat_service(self, mock_ai_service, mock_session_service):
        """创建对话服务实例"""
        return ChatService(mock_ai_service, mock_session_service)
    
    def test_init(self, mock_ai_service, mock_session_service):
        """测试初始化"""
        chat_service = ChatService(mock_ai_service, mock_session_service)
        assert chat_service.ai_service == mock_ai_service
        assert chat_service.session_service == mock_session_service
        assert len(chat_service.generation_keywords) > 0
    
    def test_send_message_success(self, chat_service, mock_session_service, mock_ai_service):
        """测试成功发送消息"""
        session_id = 'test_session_123'
        message = '我需要测试登录功能'
        
        result = chat_service.send_message(session_id, message)
        
        assert result['success'] is True
        assert result['reply'] == '这是AI的回复'
        assert result['need_more_info'] is True
        assert result['ready_to_generate'] is False
        assert result['session_status'] == 'chatting'
        
        # 验证会话服务调用
        mock_session_service.is_session_valid.assert_called_once_with(session_id)
        mock_session_service.get_session_data.assert_called_once_with(session_id)
        mock_session_service.extend_session.assert_called_once_with(session_id)
        
        # 验证AI服务调用
        mock_ai_service.chat_with_agent.assert_called_once()
    
    def test_send_message_invalid_session(self, chat_service, mock_session_service):
        """测试无效会话"""
        mock_session_service.is_session_valid.return_value = False
        
        result = chat_service.send_message('invalid_session', 'test message')
        
        assert result['success'] is False
        assert result['error'] == 'session_invalid'
        assert '会话无效' in result['message']
    
    def test_send_message_session_not_found(self, chat_service, mock_session_service):
        """测试会话数据不存在"""
        mock_session_service.get_session_data.return_value = None
        
        result = chat_service.send_message('test_session', 'test message')
        
        assert result['success'] is False
        assert result['error'] == 'session_not_found'
        assert '会话数据不存在' in result['message']
    
    def test_send_message_invalid_status(self, chat_service, mock_session_service):
        """测试无效的会话状态"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'completed',  # 不支持对话的状态
            'chat_history': []
        }
        
        result = chat_service.send_message('test_session', 'test message')
        
        assert result['success'] is False
        assert result['error'] == 'invalid_status'
        assert '当前会话状态不支持对话' in result['message']
    
    def test_send_message_generation_keyword(self, chat_service, mock_session_service):
        """测试生成关键词触发"""
        session_id = 'test_session_123'
        message = '开始生成'
        
        result = chat_service.send_message(session_id, message)
        
        assert result['success'] is True
        assert result['ready_to_generate'] is True
        assert result['need_more_info'] is False
        assert result['session_status'] == 'ready_to_generate'
        assert '开始为您生成' in result['reply']
        
        # 验证会话状态更新
        mock_session_service.update_session_data.assert_called()
        update_call = mock_session_service.update_session_data.call_args[0]
        assert update_call[0] == session_id
        assert update_call[1]['status'] == 'ready_to_generate'
    
    def test_check_generation_keywords(self, chat_service):
        """测试生成关键词检查"""
        # 中文关键词
        assert chat_service._check_generation_keywords('开始生成') is True
        assert chat_service._check_generation_keywords('请开始生成测试用例') is True
        assert chat_service._check_generation_keywords('生成用例') is True
        
        # 英文关键词
        assert chat_service._check_generation_keywords('start generation') is True
        assert chat_service._check_generation_keywords('please generate') is True
        assert chat_service._check_generation_keywords('begin') is True
        
        # 非关键词
        assert chat_service._check_generation_keywords('普通消息') is False
        assert chat_service._check_generation_keywords('测试需求') is False
    
    def test_send_message_analyzing_status(self, chat_service, mock_session_service, mock_ai_service):
        """测试analyzing状态下的消息处理"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'analyzing',
            'chat_history': [],
            'files': {},
            'config': {},
            'analysis_result': {}
        }
        
        result = chat_service.send_message('test_session', 'test message')
        
        assert result['success'] is True
        # 验证状态从analyzing更新为chatting
        mock_session_service.update_session_data.assert_called()
        update_call = mock_session_service.update_session_data.call_args[0]
        assert update_call[1]['status'] == 'chatting'
    
    def test_get_chat_history_success(self, chat_service, mock_session_service):
        """测试获取对话历史成功"""
        chat_history = [
            {'role': 'user', 'message': '消息1', 'timestamp': '2025-01-08T10:00:00Z'},
            {'role': 'ai', 'message': '回复1', 'timestamp': '2025-01-08T10:01:00Z'},
            {'role': 'user', 'message': '消息2', 'timestamp': '2025-01-08T10:02:00Z'}
        ]
        
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'chat_history': chat_history
        }
        
        result = chat_service.get_chat_history('test_session')
        
        assert result['success'] is True
        assert result['chat_history'] == chat_history
        assert result['total_messages'] == 3
    
    def test_get_chat_history_with_limit(self, chat_service, mock_session_service):
        """测试限制数量的对话历史获取"""
        chat_history = [
            {'role': 'user', 'message': '消息1'},
            {'role': 'ai', 'message': '回复1'},
            {'role': 'user', 'message': '消息2'},
            {'role': 'ai', 'message': '回复2'}
        ]
        
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'chat_history': chat_history
        }
        
        result = chat_service.get_chat_history('test_session', limit=2)
        
        assert result['success'] is True
        assert len(result['chat_history']) == 2
        assert result['chat_history'] == chat_history[-2:]  # 最后2条消息
        assert result['total_messages'] == 4
    
    def test_clear_chat_history_success(self, chat_service, mock_session_service):
        """测试清空对话历史成功"""
        result = chat_service.clear_chat_history('test_session')
        
        assert result['success'] is True
        assert '对话历史已清空' in result['message']
        
        # 验证会话数据更新
        mock_session_service.update_session_data.assert_called()
        update_call = mock_session_service.update_session_data.call_args[0]
        assert update_call[0] == 'test_session'
        assert update_call[1]['chat_history'] == []
    
    def test_clear_chat_history_invalid_session(self, chat_service, mock_session_service):
        """测试清空无效会话的对话历史"""
        mock_session_service.is_session_valid.return_value = False
        
        result = chat_service.clear_chat_history('invalid_session')
        
        assert result['success'] is False
        assert result['error'] == 'session_invalid'
    
    def test_build_chat_context(self, chat_service):
        """测试构建对话上下文"""
        session_data = {
            'session_id': 'test_session',
            'status': 'chatting',
            'chat_history': [
                {'role': 'user', 'message': '消息1'},
                {'role': 'ai', 'message': '回复1'}
            ],
            'files': {'template': 'file1', 'history': 'file2'},
            'config': {'api_version': 'v2.0'},
            'analysis_result': {'template_info': '分析结果'}
        }
        
        context = chat_service._build_chat_context(session_data)
        
        assert context['session_id'] == 'test_session'
        assert context['status'] == 'chatting'
        assert len(context['chat_history']) == 2
        assert len(context['files_info']) == 2
        assert context['config']['api_version'] == 'v2.0'
        assert context['analysis_result']['template_info'] == '分析结果'
        
        # 验证统计信息
        stats = context['stats']
        assert stats['total_messages'] == 2
        assert stats['user_messages'] == 1
        assert stats['ai_messages'] == 1
        assert stats['files_count'] == 2
    
    def test_get_session_status_success(self, chat_service, mock_session_service):
        """测试获取会话状态成功"""
        session_data = {
            'session_id': 'test_session',
            'status': 'chatting',
            'created_at': '2025-01-08T10:00:00Z',
            'updated_at': '2025-01-08T10:30:00Z',
            'chat_history': [{'role': 'user', 'message': 'test'}],
            'files': {'template': 'file1'}
        }
        
        mock_session_service.get_session_data.return_value = session_data
        
        result = chat_service.get_session_status('test_session')
        
        assert result['success'] is True
        status_info = result['status_info']
        assert status_info['session_id'] == 'test_session'
        assert status_info['status'] == 'chatting'
        assert status_info['message_count'] == 1
        assert status_info['files_uploaded'] == 1
        assert status_info['ready_to_generate'] is False
    
    def test_get_session_status_ready_to_generate(self, chat_service, mock_session_service):
        """测试准备生成状态的会话状态"""
        session_data = {
            'session_id': 'test_session',
            'status': 'ready_to_generate',
            'chat_history': [],
            'files': {}
        }
        
        mock_session_service.get_session_data.return_value = session_data
        
        result = chat_service.get_session_status('test_session')
        
        assert result['success'] is True
        assert result['status_info']['ready_to_generate'] is True
    
    def test_reset_session_status_success(self, chat_service, mock_session_service):
        """测试重置会话状态成功"""
        result = chat_service.reset_session_status('test_session', 'analyzing')
        
        assert result['success'] is True
        assert 'analyzing' in result['message']
        
        # 验证状态更新
        mock_session_service.update_session_data.assert_called()
        update_call = mock_session_service.update_session_data.call_args[0]
        assert update_call[0] == 'test_session'
        assert update_call[1]['status'] == 'analyzing'
    
    def test_reset_session_status_invalid_session(self, chat_service, mock_session_service):
        """测试重置无效会话状态"""
        mock_session_service.is_session_valid.return_value = False
        
        result = chat_service.reset_session_status('invalid_session')
        
        assert result['success'] is False
        assert result['error'] == 'session_invalid'
    
    def test_add_message_to_history(self, chat_service, mock_session_service):
        """测试添加消息到历史"""
        session_id = 'test_session'
        role = 'user'
        message = '测试消息'
        
        chat_service._add_message_to_history(session_id, role, message)
        
        # 验证调用会话服务的添加消息方法
        mock_session_service.add_chat_message.assert_called_once()
        call_args = mock_session_service.add_chat_message.call_args[0]
        assert call_args[0] == session_id
        assert call_args[1] == role
        assert call_args[2] == message
    
    def test_send_message_exception_handling(self, chat_service, mock_session_service, mock_ai_service):
        """测试发送消息异常处理"""
        # Mock AI服务抛出异常
        mock_ai_service.chat_with_agent.side_effect = Exception('AI服务异常')
        
        result = chat_service.send_message('test_session', 'test message')
        
        assert result['success'] is False
        assert result['error'] == 'chat_error'
        assert '对话处理失败' in result['message']


class TestChatServiceIntegration:
    """对话服务集成测试"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI服务"""
        ai_service = Mock(spec=AIService)
        return ai_service
    
    @pytest.fixture
    def mock_session_service(self):
        """Mock 会话服务"""
        session_service = Mock(spec=SessionService)
        session_service.is_session_valid.return_value = True
        return session_service
    
    @pytest.fixture
    def chat_service(self, mock_ai_service, mock_session_service):
        """创建对话服务实例"""
        return ChatService(mock_ai_service, mock_session_service)
    
    def test_complete_chat_workflow(self, chat_service, mock_session_service, mock_ai_service):
        """测试完整的对话工作流"""
        session_id = 'integration_test_session'
        
        # 设置初始会话数据
        initial_session_data = {
            'session_id': session_id,
            'status': 'analyzing',
            'chat_history': [],
            'files': {'template': 'file1'},
            'config': {'api_version': 'v2.0'},
            'analysis_result': {'template_info': '分析完成'}
        }
        
        mock_session_service.get_session_data.return_value = initial_session_data
        
        # 1. 第一次对话 - 从analyzing状态开始
        mock_ai_service.chat_with_agent.return_value = {
            'reply': '请描述您的测试需求',
            'need_more_info': True,
            'ready_to_generate': False,
            'suggestions': ['描述功能模块', '说明测试场景']
        }
        
        result1 = chat_service.send_message(session_id, '我需要测试登录功能')
        
        assert result1['success'] is True
        assert result1['need_more_info'] is True
        assert result1['ready_to_generate'] is False
        
        # 验证状态从analyzing更新为chatting
        update_calls = mock_session_service.update_session_data.call_args_list
        assert any(call[0][1]['status'] == 'chatting' for call in update_calls)
        
        # 2. 第二次对话 - 继续收集需求
        mock_session_service.get_session_data.return_value = {
            **initial_session_data,
            'status': 'chatting',
            'chat_history': [
                {'role': 'user', 'message': '我需要测试登录功能'},
                {'role': 'ai', 'message': '请描述您的测试需求'}
            ]
        }
        
        mock_ai_service.chat_with_agent.return_value = {
            'reply': '还需要了解更多细节吗？如果准备好了，请回复"开始生成"',
            'need_more_info': True,
            'ready_to_generate': False
        }
        
        result2 = chat_service.send_message(session_id, '包括正常登录和异常场景')
        
        assert result2['success'] is True
        assert result2['need_more_info'] is True
        
        # 3. 触发生成关键词
        result3 = chat_service.send_message(session_id, '开始生成')
        
        assert result3['success'] is True
        assert result3['ready_to_generate'] is True
        assert result3['need_more_info'] is False
        assert result3['session_status'] == 'ready_to_generate'
        
        # 验证状态更新为ready_to_generate
        final_update_calls = mock_session_service.update_session_data.call_args_list
        assert any(call[0][1]['status'] == 'ready_to_generate' for call in final_update_calls)
        
        # 4. 验证会话历史管理
        history_result = chat_service.get_chat_history(session_id)
        assert history_result['success'] is True
        
        # 5. 验证会话状态查询
        status_result = chat_service.get_session_status(session_id)
        assert status_result['success'] is True
        
        # 验证所有会话服务调用
        assert mock_session_service.is_session_valid.call_count >= 3
        assert mock_session_service.extend_session.call_count >= 2  # 生成关键词触发时不调用extend_session
        assert mock_session_service.add_chat_message.call_count >= 6  # 每次对话添加2条消息
    
    def test_error_recovery_workflow(self, chat_service, mock_session_service, mock_ai_service):
        """测试错误恢复工作流"""
        session_id = 'error_test_session'
        
        # 设置会话数据
        mock_session_service.get_session_data.return_value = {
            'session_id': session_id,
            'status': 'chatting',
            'chat_history': [],
            'files': {},
            'config': {},
            'analysis_result': {}
        }
        
        # 1. AI服务异常，应该返回错误
        mock_ai_service.chat_with_agent.side_effect = Exception('AI服务不可用')
        
        result = chat_service.send_message(session_id, 'test message')
        
        assert result['success'] is False
        assert result['error'] == 'chat_error'
        
        # 2. 恢复AI服务，继续正常对话
        mock_ai_service.chat_with_agent.side_effect = None
        mock_ai_service.chat_with_agent.return_value = {
            'reply': '服务已恢复，请继续',
            'need_more_info': True,
            'ready_to_generate': False
        }
        
        result = chat_service.send_message(session_id, 'test message again')
        
        assert result['success'] is True
        assert '服务已恢复' in result['reply']
        
        # 3. 会话状态管理
        status_result = chat_service.get_session_status(session_id)
        assert status_result['success'] is True
        
        # 4. 重置会话状态
        reset_result = chat_service.reset_session_status(session_id, 'analyzing')
        assert reset_result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])