import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from services.generation_service import GenerationService
from services.file_service import FileService
from services.session_service import SessionService
from services.ai_service import AIService


class TestGenerationService:
    """生成服务单元测试"""
    
    @pytest.fixture
    def mock_file_service(self):
        """Mock文件服务"""
        file_service = Mock(spec=FileService)
        file_service.save_uploaded_file.return_value = {
            'file_id': 'template_123',
            'original_name': 'template.xml',
            'file_path': '/path/to/file.xml',
            'file_size': 1024
        }
        file_service.generate_xml_output.return_value = '<?xml version="1.0"?><testcases></testcases>'
        file_service.save_generated_file.return_value = {
            'file_id': 'generated_456',
            'filename': 'test_cases.xml',
            'file_path': '/path/to/generated.xml',
            'file_size': 2048
        }
        file_service.get_file_info.return_value = {
            'file_id': 'generated_456',
            'filename': 'test_cases.xml',
            'file_path': '/path/to/generated.xml',
            'file_size': 2048
        }
        file_service.get_file_content.return_value = b'<?xml version="1.0"?><testcases></testcases>'
        file_service.cleanup_session_files.return_value = True
        return file_service
    
    @pytest.fixture
    def mock_session_service(self):
        """Mock会话服务"""
        session_service = Mock(spec=SessionService)
        session_service.create_session.return_value = {
            'success': True,
            'session_id': 'test_session_123'
        }
        session_service.is_session_valid.return_value = True
        session_service.get_session_data.return_value = {
            'session_id': 'test_session_123',
            'status': 'ready_to_generate',
            'files': {},
            'config': {},
            'analysis_result': {},
            'chat_history': [],
            'generated_file_id': 'generated_456'
        }
        session_service.update_session_data.return_value = {'success': True}
        session_service.delete_session.return_value = {'success': True}
        return session_service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI服务"""
        ai_service = Mock(spec=AIService)
        ai_service.analyze_files.return_value = {
            'template_info': '检测到模板包含20个测试场景',
            'history_info': '检测到50条历史用例',
            'suggestions': ['建议1', '建议2']
        }
        ai_service.generate_test_cases.return_value = iter([
            {
                'type': 'progress',
                'data': {
                    'stage': 'analyzing',
                    'message': '正在分析...',
                    'progress': 25
                }
            },
            {
                'type': 'complete',
                'data': {
                    'test_cases': [
                        {
                            'id': 'TC001',
                            'name': '测试用例1',
                            'steps': [],
                            'preconditions': [],
                            'expectedResults': []
                        }
                    ],
                    'total_count': 1,
                    'message': '生成完成'
                }
            }
        ])
        return ai_service
    
    @pytest.fixture
    def generation_service(self, mock_file_service, mock_session_service, mock_ai_service):
        """创建生成服务实例"""
        return GenerationService(mock_file_service, mock_session_service, mock_ai_service)
    
    @pytest.fixture
    def mock_file_storage(self):
        """Mock文件存储对象"""
        file_storage = Mock()
        file_storage.filename = 'template.xml'
        return file_storage
    
    def test_init(self, mock_file_service, mock_session_service, mock_ai_service):
        """测试初始化"""
        service = GenerationService(mock_file_service, mock_session_service, mock_ai_service)
        assert service.file_service == mock_file_service
        assert service.session_service == mock_session_service
        assert service.ai_service == mock_ai_service
    
    def test_start_generation_task_success(self, generation_service, mock_file_storage):
        """测试成功启动生成任务"""
        files = {'case_template': mock_file_storage}
        config = {'api_version': 'v2.0'}
        
        result = generation_service.start_generation_task(files, config)
        
        assert result['success'] is True
        assert 'session_id' in result
        assert 'message' in result
        assert 'initial_analysis' in result
        assert result['files_processed'] == 1
    
    def test_start_generation_task_session_creation_failed(self, generation_service, mock_session_service, mock_file_storage):
        """测试会话创建失败"""
        mock_session_service.create_session.side_effect = Exception("Session creation failed")
        
        files = {'case_template': mock_file_storage}
        config = {'api_version': 'v2.0'}
        
        result = generation_service.start_generation_task(files, config)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_start_generation_task_missing_required_file(self, generation_service):
        """测试缺少必需文件"""
        files = {'history_case': Mock()}  # 缺少case_template
        config = {'api_version': 'v2.0'}
        
        result = generation_service.start_generation_task(files, config)
        
        assert result['success'] is False
        assert result['error'] == 'missing_required_file'
    
    def test_start_generation_task_file_save_failed(self, generation_service, mock_file_service, mock_file_storage):
        """测试文件保存失败"""
        mock_file_service.save_uploaded_file.side_effect = Exception('文件保存失败')
        
        files = {'case_template': mock_file_storage}
        config = {'api_version': 'v2.0'}
        
        result = generation_service.start_generation_task(files, config)
        
        assert result['success'] is False
        assert result['error'] == 'file_save_failed'
    
    def test_generate_test_cases_stream_success(self, generation_service):
        """测试成功流式生成测试用例"""
        session_id = 'test_session_123'
        
        responses = list(generation_service.generate_test_cases_stream(session_id))
        
        assert len(responses) >= 2  # 至少有状态和完成响应
        
        # 验证状态响应
        status_response = responses[0]
        assert status_response['type'] == 'status'
        assert status_response['data']['status'] == 'generating'
        
        # 验证完成响应
        complete_responses = [r for r in responses if r.get('type') == 'complete']
        assert len(complete_responses) == 1
        assert 'test_cases' in complete_responses[0]['data']
    
    def test_generate_test_cases_stream_invalid_session(self, generation_service, mock_session_service):
        """测试无效会话的流式生成"""
        mock_session_service.is_session_valid.return_value = False
        
        responses = list(generation_service.generate_test_cases_stream('invalid_session'))
        
        assert len(responses) == 1
        assert responses[0]['type'] == 'error'
        assert responses[0]['data']['error'] == 'session_invalid'
    
    def test_generate_test_cases_stream_invalid_status(self, generation_service, mock_session_service):
        """测试无效状态的流式生成"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'analyzing'  # 不是ready_to_generate
        }
        
        responses = list(generation_service.generate_test_cases_stream('test_session'))
        
        assert len(responses) == 1
        assert responses[0]['type'] == 'error'
        assert responses[0]['data']['error'] == 'invalid_status'
    
    def test_finalize_test_cases_success(self, generation_service, mock_session_service):
        """测试成功确认测试用例"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'generated'
        }
        
        test_cases = [
            {
                'id': 'TC001',
                'name': '测试用例1',
                'steps': [],
                'preconditions': [],
                'expectedResults': []
            }
        ]
        
        result = generation_service.finalize_test_cases('test_session', test_cases)
        
        assert result['success'] is True
        assert 'file_id' in result
        assert 'filename' in result
        assert result['test_cases_count'] == 1
    
    def test_finalize_test_cases_invalid_session(self, generation_service, mock_session_service):
        """测试无效会话的确认操作"""
        mock_session_service.is_session_valid.return_value = False
        
        result = generation_service.finalize_test_cases('invalid_session', [])
        
        assert result['success'] is False
        assert result['error'] == 'session_invalid'
    
    def test_finalize_test_cases_invalid_status(self, generation_service, mock_session_service):
        """测试无效状态的确认操作"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'analyzing'  # 不支持确认操作的状态
        }
        
        result = generation_service.finalize_test_cases('test_session', [])
        
        assert result['success'] is False
        assert result['error'] == 'invalid_status'
    
    def test_finalize_test_cases_invalid_data(self, generation_service, mock_session_service):
        """测试无效测试用例数据"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'status': 'generated'
        }
        
        result = generation_service.finalize_test_cases('test_session', None)
        
        assert result['success'] is False
        assert result['error'] == 'invalid_test_cases'
    
    def test_get_generated_file_success(self, generation_service):
        """测试成功获取生成文件"""
        session_id = 'test_session_123'
        file_id = 'generated_456'
        
        result = generation_service.get_generated_file(session_id, file_id)
        
        assert result['success'] is True
        assert 'file_info' in result
        assert 'file_content' in result
        assert result['content_type'] == 'application/xml'
    
    def test_get_generated_file_access_denied(self, generation_service, mock_session_service):
        """测试文件访问权限拒绝"""
        mock_session_service.get_session_data.return_value = {
            'session_id': 'test_session',
            'generated_file_id': 'other_file_id'  # 不匹配请求的file_id
        }
        
        result = generation_service.get_generated_file('test_session', 'generated_456')
        
        assert result['success'] is False
        assert result['error'] == 'file_access_denied'
    
    def test_get_generation_status_success(self, generation_service):
        """测试成功获取生成状态"""
        session_id = 'test_session_123'
        
        result = generation_service.get_generation_status(session_id)
        
        assert result['success'] is True
        assert 'status_info' in result
        
        status_info = result['status_info']
        assert status_info['session_id'] == session_id
        assert 'status' in status_info
        assert 'files_uploaded' in status_info
        assert 'has_test_cases' in status_info
    
    def test_cleanup_session_success(self, generation_service):
        """测试成功清理会话"""
        session_id = 'test_session_123'
        
        result = generation_service.cleanup_session(session_id)
        
        assert result['success'] is True
        assert 'file_cleanup' in result
        assert 'session_cleanup' in result
    
    def test_build_initial_message(self, generation_service):
        """测试构建初始消息"""
        analysis_result = {
            'template_info': '检测到模板包含20个测试场景',
            'history_info': '检测到50条历史用例',
            'suggestions': ['建议1', '建议2']
        }
        
        message = generation_service._build_initial_message(analysis_result)
        
        assert '文件分析完成' in message
        assert '20个测试场景' in message
        assert '50条历史用例' in message
        assert '请描述您希望生成的测试用例类型' in message
    
    def test_build_generation_context(self, generation_service):
        """测试构建生成上下文"""
        session_data = {
            'session_id': 'test_session',
            'files': {'template': 'file1'},
            'config': {'api_version': 'v2.0'},
            'analysis_result': {'template_info': '分析结果'},
            'chat_history': [
                {'role': 'user', 'message': '我需要测试需求1'},
                {'role': 'ai', 'message': '回复1'},
                {'role': 'user', 'message': '我需要测试需求2'}
            ]
        }
        
        context = generation_service._build_generation_context(session_data)
        
        assert context['session_id'] == 'test_session'
        assert context['files_info'] == {'template': 'file1'}
        assert context['config']['api_version'] == 'v2.0'
        assert len(context['requirements']) == 2  # 只提取用户消息
        assert '我需要测试需求1' in context['requirements']
        assert '我需要测试需求2' in context['requirements']
    
    def test_extract_requirements_from_chat(self, generation_service):
        """测试从对话历史提取需求"""
        chat_history = [
            {'role': 'user', 'message': '我需要测试登录功能'},
            {'role': 'ai', 'message': 'AI回复'},
            {'role': 'user', 'message': '包括异常场景'},
            {'role': 'user', 'message': '短'},  # 太短的消息应该被过滤
            {'role': 'user', 'message': '还需要测试权限控制'}
        ]
        
        requirements = generation_service._extract_requirements_from_chat(chat_history)
        
        assert len(requirements) == 3
        assert '我需要测试登录功能' in requirements
        assert '包括异常场景' in requirements
        assert '还需要测试权限控制' in requirements
        assert '短' not in requirements  # 被过滤掉


class TestGenerationServiceIntegration:
    """生成服务集成测试"""
    
    @pytest.fixture
    def mock_services(self):
        """创建Mock服务"""
        file_service = Mock(spec=FileService)
        session_service = Mock(spec=SessionService)
        ai_service = Mock(spec=AIService)
        
        # 设置基本返回值
        session_service.create_session.return_value = {
            'success': True,
            'session_id': 'integration_test_session'
        }
        session_service.is_session_valid.return_value = True
        session_service.update_session_data.return_value = {'success': True}
        session_service.delete_session.return_value = {'success': True}
        
        file_service.save_uploaded_file.return_value = {
            'file_id': 'template_123',
            'original_name': 'template.xml',
            'file_path': '/path/to/file.xml',
            'file_size': 1024
        }
        file_service.generate_xml_output.return_value = '<?xml version="1.0"?><testcases></testcases>'
        file_service.save_generated_file.return_value = {
            'file_id': 'generated_456',
            'filename': 'test_cases.xml',
            'file_path': '/path/to/generated.xml',
            'file_size': 2048
        }
        file_service.cleanup_session_files.return_value = True
        
        ai_service.analyze_files.return_value = {
            'template_info': '检测到模板包含20个测试场景',
            'history_info': '检测到50条历史用例',
            'suggestions': ['建议1', '建议2']
        }
        
        return file_service, session_service, ai_service
    
    @pytest.fixture
    def generation_service(self, mock_services):
        """创建生成服务实例"""
        file_service, session_service, ai_service = mock_services
        return GenerationService(file_service, session_service, ai_service)
    
    def test_complete_generation_workflow(self, generation_service, mock_services):
        """测试完整的生成工作流"""
        file_service, session_service, ai_service = mock_services
        
        # 1. 启动生成任务
        mock_file = Mock()
        mock_file.filename = 'template.xml'
        
        files = {'case_template': mock_file}
        config = {'api_version': 'v2.0'}
        
        start_result = generation_service.start_generation_task(files, config)
        assert start_result['success'] is True
        session_id = start_result['session_id']
        
        # 2. 设置会话状态为准备生成
        session_service.get_session_data.return_value = {
            'session_id': session_id,
            'status': 'ready_to_generate',
            'files': {'case_template': {'file_id': 'template_123'}},
            'config': config,
            'analysis_result': {'template_info': '分析完成'},
            'chat_history': [
                {'role': 'user', 'message': '我需要测试登录功能'},
                {'role': 'user', 'message': '包括异常场景'}
            ]
        }
        
        # 3. 设置AI服务流式生成
        ai_service.generate_test_cases.return_value = iter([
            {
                'type': 'progress',
                'data': {
                    'stage': 'analyzing',
                    'message': '正在分析...',
                    'progress': 25
                }
            },
            {
                'type': 'progress',
                'data': {
                    'stage': 'generating',
                    'message': '正在生成...',
                    'progress': 75
                }
            },
            {
                'type': 'complete',
                'data': {
                    'test_cases': [
                        {
                            'id': 'TC001',
                            'name': '登录功能测试',
                            'steps': [{'name': '输入用户名'}],
                            'preconditions': [],
                            'expectedResults': [{'name': '登录成功'}]
                        },
                        {
                            'id': 'TC002',
                            'name': '登录异常测试',
                            'steps': [{'name': '输入错误密码'}],
                            'preconditions': [],
                            'expectedResults': [{'name': '显示错误信息'}]
                        }
                    ],
                    'total_count': 2,
                    'message': '生成完成'
                }
            }
        ])
        
        # 4. 流式生成测试用例
        responses = list(generation_service.generate_test_cases_stream(session_id))
        
        # 验证响应
        assert len(responses) >= 3  # 状态 + 进度 + 完成
        
        status_responses = [r for r in responses if r.get('type') == 'status']
        assert len(status_responses) == 1
        
        progress_responses = [r for r in responses if r.get('type') == 'progress']
        assert len(progress_responses) == 2
        
        complete_responses = [r for r in responses if r.get('type') == 'complete']
        assert len(complete_responses) == 1
        
        test_cases = complete_responses[0]['data']['test_cases']
        assert len(test_cases) == 2
        
        # 5. 设置会话状态为已生成
        session_service.get_session_data.return_value = {
            'session_id': session_id,
            'status': 'generated',
            'test_cases': test_cases
        }
        
        # 6. 确认并生成最终文件
        finalize_result = generation_service.finalize_test_cases(session_id, test_cases)
        assert finalize_result['success'] is True
        assert finalize_result['test_cases_count'] == 2
        
        # 7. 验证服务调用
        assert session_service.create_session.called
        assert file_service.save_uploaded_file.called
        assert ai_service.analyze_files.called
        assert ai_service.generate_test_cases.called
        assert file_service.generate_xml_output.called
        assert file_service.save_generated_file.called
        
        # 8. 清理会话
        cleanup_result = generation_service.cleanup_session(session_id)
        assert cleanup_result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])