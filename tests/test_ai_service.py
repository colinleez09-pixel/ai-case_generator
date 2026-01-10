import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from services.ai_service import AIService


class TestAIService:
    """AI服务单元测试"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock配置"""
        return {
            'dify_url': 'https://api.dify.ai',
            'dify_token': 'test_token',
            'mock_mode': True,
            'timeout': 30,
            'max_retries': 3
        }
    
    @pytest.fixture
    def ai_service(self, mock_config):
        """创建AI服务实例"""
        return AIService(mock_config)
    
    @pytest.fixture
    def sample_files_info(self):
        """示例文件信息"""
        return {
            'case_template': {
                'file_id': 'template_123',
                'original_name': 'template.xml',
                'file_size': 1024
            },
            'history_case': {
                'file_id': 'history_456',
                'original_name': 'history.xml',
                'file_size': 2048
            }
        }
    
    def test_init_mock_mode(self, mock_config):
        """测试Mock模式初始化"""
        service = AIService(mock_config)
        assert service.mock_mode is True
        assert service.dify_url == 'https://api.dify.ai'
        assert service.dify_token == 'test_token'
        assert service.timeout == 30
        assert service.max_retries == 3
    
    def test_init_real_mode(self, mock_config):
        """测试真实模式初始化"""
        mock_config['mock_mode'] = False
        service = AIService(mock_config)
        assert service.mock_mode is False
    
    def test_analyze_files_mock_mode(self, ai_service, sample_files_info):
        """测试Mock模式文件分析"""
        result = ai_service.analyze_files(sample_files_info)
        
        assert 'template_info' in result
        assert 'history_info' in result
        assert 'suggestions' in result
        assert isinstance(result['suggestions'], list)
        assert len(result['suggestions']) > 0
        
        # 验证模板文件信息
        assert '测试场景' in result['template_info']
        assert '历史用例' in result['history_info']
    
    def test_analyze_files_with_aw_template(self, ai_service):
        """测试包含AW模板的文件分析"""
        files_info = {
            'case_template': {'file_id': 'template_123'},
            'aw_template': {'file_id': 'aw_789'}
        }
        
        result = ai_service.analyze_files(files_info)
        
        # 验证AW模板建议
        suggestions = result['suggestions']
        aw_suggestion = any('AW工程模板' in s for s in suggestions)
        assert aw_suggestion is True
    
    def test_chat_with_agent_mock_mode(self, ai_service):
        """测试Mock模式对话"""
        session_id = 'test_session_123'
        message = '我需要测试登录功能'
        context = {'chat_history': []}
        
        result = ai_service.chat_with_agent(session_id, message, context)
        
        assert 'reply' in result
        assert 'need_more_info' in result
        assert 'ready_to_generate' in result
        assert isinstance(result['reply'], str)
        assert len(result['reply']) > 0
    
    def test_chat_with_generation_keyword(self, ai_service):
        """测试生成关键词触发"""
        session_id = 'test_session_123'
        message = '开始生成'
        context = {'chat_history': []}
        
        result = ai_service.chat_with_agent(session_id, message, context)
        
        assert result['ready_to_generate'] is True
        assert result['need_more_info'] is False
        assert '开始为您生成' in result['reply']
    
    def test_chat_with_english_generation_keyword(self, ai_service):
        """测试英文生成关键词"""
        session_id = 'test_session_123'
        message = 'start generation'
        context = {'chat_history': []}
        
        result = ai_service.chat_with_agent(session_id, message, context)
        
        assert result['ready_to_generate'] is True
    
    def test_chat_response_progression(self, ai_service):
        """测试对话响应的递进"""
        session_id = 'test_session_123'
        context = {'chat_history': []}
        
        # 第一次对话
        result1 = ai_service.chat_with_agent(session_id, '测试需求1', context)
        reply1 = result1['reply']
        
        # 模拟对话历史增长
        context['chat_history'] = [
            {'role': 'user', 'message': '测试需求1'},
            {'role': 'ai', 'message': reply1}
        ]
        
        # 第二次对话
        result2 = ai_service.chat_with_agent(session_id, '测试需求2', context)
        reply2 = result2['reply']
        
        # 验证回复不同
        assert reply1 != reply2
    
    def test_generate_test_cases_mock_stream(self, ai_service):
        """测试Mock模式流式生成"""
        session_id = 'test_session_123'
        context = {'files_info': {}, 'chat_history': []}
        
        responses = list(ai_service.generate_test_cases(session_id, context))
        
        # 验证流式响应结构
        assert len(responses) > 0
        
        # 验证进度响应
        progress_responses = [r for r in responses if r.get('type') == 'progress']
        assert len(progress_responses) > 0
        
        for progress in progress_responses:
            assert 'data' in progress
            assert 'stage' in progress['data']
            assert 'message' in progress['data']
            assert 'progress' in progress['data']
            assert 0 <= progress['data']['progress'] <= 100
        
        # 验证完成响应
        complete_responses = [r for r in responses if r.get('type') == 'complete']
        assert len(complete_responses) == 1
        
        complete_response = complete_responses[0]
        assert 'data' in complete_response
        assert 'test_cases' in complete_response['data']
        assert 'total_count' in complete_response['data']
        assert isinstance(complete_response['data']['test_cases'], list)
    
    def test_generate_mock_test_cases_structure(self, ai_service):
        """测试生成的Mock测试用例结构"""
        context = {'files_info': {}, 'chat_history': []}
        test_cases = ai_service._generate_mock_test_cases(context)
        
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0
        
        # 验证测试用例结构
        for tc in test_cases:
            assert 'id' in tc
            assert 'name' in tc
            assert 'preconditions' in tc
            assert 'steps' in tc
            assert 'expectedResults' in tc
            
            # 验证预置条件结构
            for pre in tc['preconditions']:
                assert 'id' in pre
                assert 'name' in pre
                assert 'components' in pre
                assert isinstance(pre['components'], list)
            
            # 验证步骤结构
            for step in tc['steps']:
                assert 'id' in step
                assert 'name' in step
                assert 'components' in step
                assert isinstance(step['components'], list)
            
            # 验证预期结果结构
            for result in tc['expectedResults']:
                assert 'id' in result
                assert 'name' in result
                assert 'components' in result
                assert isinstance(result['components'], list)
    
    def test_health_check_mock_mode(self, ai_service):
        """测试Mock模式健康检查"""
        result = ai_service.health_check()
        
        assert result['status'] == 'healthy'
        assert result['mode'] == 'mock'
        assert 'message' in result
    
    @patch('requests.get')
    def test_health_check_real_mode_success(self, mock_get, mock_config):
        """测试真实模式健康检查成功"""
        mock_config['mock_mode'] = False
        ai_service = AIService(mock_config)
        
        # Mock成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = ai_service.health_check()
        
        assert result['status'] == 'healthy'
        assert result['mode'] == 'dify'
        assert 'Dify服务连接正常' in result['message']
    
    @patch('requests.get')
    def test_health_check_real_mode_failure(self, mock_get, mock_config):
        """测试真实模式健康检查失败"""
        mock_config['mock_mode'] = False
        ai_service = AIService(mock_config)
        
        # Mock失败响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = ai_service.health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['mode'] == 'dify'
        assert '响应异常' in result['message']
    
    @patch('requests.get')
    def test_health_check_connection_error(self, mock_get, mock_config):
        """测试健康检查连接错误"""
        mock_config['mock_mode'] = False
        ai_service = AIService(mock_config)
        
        # Mock连接异常
        mock_get.side_effect = Exception('Connection failed')
        
        result = ai_service.health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['mode'] == 'dify'
        assert '连接失败' in result['message']
    
    @patch('requests.post')
    def test_dify_analyze_files_success(self, mock_post, mock_config):
        """测试Dify文件分析成功"""
        mock_config['mock_mode'] = False
        ai_service = AIService(mock_config)
        
        # Mock成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'answer': json.dumps({
                'template_info': '分析完成',
                'history_info': '历史文件分析',
                'suggestions': ['建议1', '建议2']
            })
        }
        mock_post.return_value = mock_response
        
        files_info = {'template': {'file_id': 'test'}}
        result = ai_service._dify_analyze_files(files_info)
        
        assert result['template_info'] == '分析完成'
        assert result['history_info'] == '历史文件分析'
        assert len(result['suggestions']) == 2
    
    @patch('requests.post')
    def test_dify_analyze_files_failure(self, mock_post, mock_config):
        """测试Dify文件分析失败"""
        mock_config['mock_mode'] = False
        ai_service = AIService(mock_config)
        
        # Mock失败响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        files_info = {'template': {'file_id': 'test'}}
        
        with pytest.raises(Exception):
            ai_service._dify_analyze_files(files_info)
    
    def test_analyze_files_fallback_to_mock(self, ai_service):
        """测试分析文件失败时降级到Mock模式"""
        # 临时设置为非Mock模式
        ai_service.mock_mode = False
        
        # Mock Dify方法抛出异常
        with patch.object(ai_service, '_dify_analyze_files', side_effect=Exception('Dify error')):
            files_info = {'template': {'file_id': 'test'}}
            result = ai_service.analyze_files(files_info)
            
            # 验证降级到Mock模式
            assert 'template_info' in result
            assert 'suggestions' in result
    
    def test_chat_fallback_to_mock(self, ai_service):
        """测试对话失败时降级到Mock模式"""
        # 临时设置为非Mock模式
        ai_service.mock_mode = False
        
        # Mock Dify方法抛出异常
        with patch.object(ai_service, '_dify_chat_request', side_effect=Exception('Dify error')):
            result = ai_service.chat_with_agent('session_123', 'test message', {})
            
            # 验证降级到Mock模式
            assert 'reply' in result
            assert 'need_more_info' in result
    
    def test_generation_fallback_to_mock(self, ai_service):
        """测试生成失败时降级到Mock模式"""
        # 临时设置为非Mock模式
        ai_service.mock_mode = False
        
        # Mock Dify方法抛出异常
        with patch.object(ai_service, '_dify_generation_stream', side_effect=Exception('Dify error')):
            responses = list(ai_service.generate_test_cases('session_123', {}))
            
            # 验证降级到Mock模式
            assert len(responses) > 0
            complete_responses = [r for r in responses if r.get('type') == 'complete']
            assert len(complete_responses) == 1


class TestAIServiceIntegration:
    """AI服务集成测试"""
    
    @pytest.fixture
    def ai_service(self):
        """创建AI服务实例"""
        config = {
            'dify_url': 'https://api.dify.ai',
            'dify_token': 'test_token',
            'mock_mode': True,
            'timeout': 30,
            'max_retries': 3
        }
        return AIService(config)
    
    def test_complete_workflow(self, ai_service):
        """测试完整的AI服务工作流"""
        session_id = 'integration_test_session'
        
        # 1. 文件分析
        files_info = {
            'case_template': {'file_id': 'template_123'},
            'history_case': {'file_id': 'history_456'}
        }
        
        analysis_result = ai_service.analyze_files(files_info)
        assert 'template_info' in analysis_result
        assert 'history_info' in analysis_result
        
        # 2. 多轮对话
        context = {'chat_history': [], 'files_info': files_info}
        
        # 第一轮对话
        chat_result1 = ai_service.chat_with_agent(session_id, '我需要测试登录功能', context)
        assert chat_result1['need_more_info'] is True
        assert chat_result1['ready_to_generate'] is False
        
        # 更新上下文
        context['chat_history'].append({
            'role': 'user',
            'message': '我需要测试登录功能'
        })
        context['chat_history'].append({
            'role': 'ai',
            'message': chat_result1['reply']
        })
        
        # 第二轮对话
        chat_result2 = ai_service.chat_with_agent(session_id, '包括正常登录和异常场景', context)
        assert chat_result2['need_more_info'] is True
        
        # 触发生成
        chat_result3 = ai_service.chat_with_agent(session_id, '开始生成', context)
        assert chat_result3['ready_to_generate'] is True
        assert chat_result3['need_more_info'] is False
        
        # 3. 生成测试用例
        generation_responses = list(ai_service.generate_test_cases(session_id, context))
        
        # 验证生成流程
        assert len(generation_responses) > 0
        
        # 验证最终结果
        complete_response = None
        for response in generation_responses:
            if response.get('type') == 'complete':
                complete_response = response
                break
        
        assert complete_response is not None
        assert 'test_cases' in complete_response['data']
        assert len(complete_response['data']['test_cases']) > 0
        
        # 验证测试用例质量
        test_cases = complete_response['data']['test_cases']
        for tc in test_cases:
            assert tc['id'].startswith('TC')
            assert len(tc['name']) > 0
            assert len(tc['steps']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])