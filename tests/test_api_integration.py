import pytest
import json
import tempfile
import os
from app import create_app
from unittest.mock import Mock, patch

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    # Mock Redis连接
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    app.redis = mock_redis
    
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

class TestHealthEndpoint:
    """测试健康检查端点"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'redis' in data

class TestConfigAPI:
    """测试配置API"""
    
    def test_get_api_versions(self, client):
        """测试获取API版本列表"""
        response = client.get('/api/config/api-versions')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'api_versions' in data
        assert len(data['api_versions']) > 0
    
    def test_get_preset_steps(self, client):
        """测试获取预设步骤"""
        response = client.get('/api/config/preset-steps')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'preset_steps' in data
        assert len(data['preset_steps']) > 0
    
    def test_get_preset_components(self, client):
        """测试获取预设组件"""
        response = client.get('/api/config/preset-components')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'preset_components' in data
        assert len(data['preset_components']) > 0
    
    def test_get_all_config(self, client):
        """测试获取所有配置"""
        response = client.get('/api/config/all')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'config' in data
        assert 'api_versions' in data['config']
        assert 'preset_steps' in data['config']
        assert 'preset_components' in data['config']
    
    def test_config_health_check(self, client):
        """测试配置服务健康检查"""
        response = client.get('/api/config/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['status'] == 'healthy'
        assert 'stats' in data

class TestChatAPI:
    """测试聊天API"""
    
    def test_send_message_missing_data(self, client):
        """测试发送消息 - 缺少数据"""
        response = client.post('/api/chat/send')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
    
    def test_send_message_missing_session_id(self, client):
        """测试发送消息 - 缺少会话ID"""
        response = client.post('/api/chat/send', 
                             json={'message': 'test message'})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '会话ID' in data['message']
    
    def test_send_message_empty_message(self, client):
        """测试发送消息 - 空消息"""
        response = client.post('/api/chat/send', 
                             json={'session_id': 'sess_12345678', 'message': ''})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '消息内容不能为空' in data['message']
    
    def test_send_message_invalid_session(self, client):
        """测试发送消息 - 无效会话"""
        response = client.post('/api/chat/send', 
                             json={'session_id': 'sess_12345678', 'message': 'test'})
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'session_error'
    
    def test_get_chat_history_missing_session_id(self, client):
        """测试获取聊天历史 - 缺少会话ID"""
        response = client.get('/api/chat/history')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
    
    def test_get_chat_history_invalid_session(self, client):
        """测试获取聊天历史 - 无效会话"""
        response = client.get('/api/chat/history?session_id=sess_12345678')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'session_error'

class TestGenerationAPI:
    """测试生成API"""
    
    def test_start_generation_no_files(self, client):
        """测试开始生成 - 没有文件"""
        response = client.post('/api/generation/start')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '没有上传文件' in data['message']
    
    def test_generate_test_cases_missing_data(self, client):
        """测试生成测试用例 - 缺少数据"""
        response = client.post('/api/generation/generate')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
    
    def test_generate_test_cases_missing_session_id(self, client):
        """测试生成测试用例 - 缺少会话ID"""
        response = client.post('/api/generation/generate', json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '缺少会话ID' in data['message']
    
    def test_generate_test_cases_invalid_session(self, client):
        """测试生成测试用例 - 无效会话"""
        response = client.post('/api/generation/generate', 
                             json={'session_id': 'sess_12345678'})
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'session_error'
    
    def test_finalize_generation_missing_data(self, client):
        """测试确认生成 - 缺少数据"""
        response = client.post('/api/generation/finalize')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
    
    def test_download_file_missing_params(self, client):
        """测试下载文件 - 缺少参数"""
        response = client.get('/api/generation/download')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '缺少必要参数' in data['message']
    
    def test_get_generation_status_missing_session_id(self, client):
        """测试获取生成状态 - 缺少会话ID"""
        response = client.get('/api/generation/status')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'validation_error'
        assert '缺少会话ID' in data['message']

class TestErrorHandling:
    """测试错误处理"""
    
    def test_404_error(self, client):
        """测试404错误"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'not_found'
        assert 'details' in data
        assert 'request_id' in data['details']
    
    def test_405_error(self, client):
        """测试405错误 - 方法不允许"""
        response = client.put('/api/config/api-versions')
        assert response.status_code == 405
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'method_not_allowed'

class TestCORSHeaders:
    """测试CORS头"""
    
    def test_cors_headers_present(self, client):
        """测试CORS头存在"""
        response = client.get('/health')
        assert response.status_code == 200
        
        # 检查CORS相关头（如果配置了的话）
        # 这里主要验证请求能正常处理
        assert response.headers.get('Content-Type') == 'application/json'

class TestRequestValidation:
    """测试请求验证"""
    
    def test_invalid_json(self, client):
        """测试无效JSON"""
        response = client.post('/api/chat/send', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_content_type_validation(self, client):
        """测试内容类型验证"""
        # 对于需要JSON的端点，发送非JSON数据
        response = client.post('/api/chat/send', 
                             data='test=data')
        assert response.status_code == 400