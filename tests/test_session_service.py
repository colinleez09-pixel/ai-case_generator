import pytest
import json
from unittest.mock import Mock, MagicMock
from services.session_service import SessionService

@pytest.fixture
def mock_redis():
    """创建Mock Redis客户端"""
    redis_mock = Mock()
    redis_mock.setex = MagicMock(return_value=True)
    redis_mock.get = MagicMock(return_value=None)
    redis_mock.exists = MagicMock(return_value=0)
    redis_mock.delete = MagicMock(return_value=1)
    redis_mock.expire = MagicMock(return_value=True)
    redis_mock.keys = MagicMock(return_value=[])
    return redis_mock

@pytest.fixture
def session_service(mock_redis):
    """创建会话服务实例"""
    return SessionService(mock_redis, session_timeout=3600)

def test_create_session(session_service, mock_redis):
    """测试创建会话"""
    session_id = session_service.create_session()
    
    # 验证会话ID格式
    assert session_id.startswith('sess_')
    assert len(session_id) == 17  # sess_ + 12位hex
    
    # 验证Redis调用
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0].startswith('session:sess_')
    assert call_args[0][1] == 3600  # timeout
    
    # 验证存储的数据结构
    stored_data = json.loads(call_args[0][2])
    assert stored_data['session_id'] == session_id
    assert stored_data['status'] == 'created'
    assert 'created_at' in stored_data
    assert 'files' in stored_data
    assert 'chat_history' in stored_data

def test_get_session_data_exists(session_service, mock_redis):
    """测试获取存在的会话数据"""
    session_id = 'sess_test123'
    test_data = {
        'session_id': session_id,
        'status': 'created',
        'files': {}
    }
    
    mock_redis.get.return_value = json.dumps(test_data)
    
    result = session_service.get_session_data(session_id)
    
    assert result == test_data
    mock_redis.get.assert_called_once_with('session:sess_test123')

def test_get_session_data_not_exists(session_service, mock_redis):
    """测试获取不存在的会话数据"""
    mock_redis.get.return_value = None
    
    result = session_service.get_session_data('sess_notexist')
    
    assert result is None

def test_update_session_data(session_service, mock_redis):
    """测试更新会话数据"""
    session_id = 'sess_test123'
    existing_data = {
        'session_id': session_id,
        'status': 'created',
        'files': {}
    }
    
    # Mock获取现有数据
    mock_redis.get.return_value = json.dumps(existing_data)
    
    # 更新数据
    update_data = {'status': 'analyzing', 'new_field': 'value'}
    result = session_service.update_session_data(session_id, update_data)
    
    assert result is True
    
    # 验证setex被调用
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    updated_data = json.loads(call_args[0][2])
    
    assert updated_data['status'] == 'analyzing'
    assert updated_data['new_field'] == 'value'
    assert 'updated_at' in updated_data

def test_is_session_valid(session_service, mock_redis):
    """测试会话有效性检查"""
    mock_redis.exists.return_value = 1
    
    result = session_service.is_session_valid('sess_test123')
    
    assert result is True
    mock_redis.exists.assert_called_once_with('session:sess_test123')

def test_delete_session(session_service, mock_redis):
    """测试删除会话"""
    mock_redis.delete.return_value = 1
    
    result = session_service.delete_session('sess_test123')
    
    assert result is True
    mock_redis.delete.assert_called_once_with('session:sess_test123')

def test_extend_session(session_service, mock_redis):
    """测试延长会话"""
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = json.dumps({'session_id': 'sess_test123'})
    
    result = session_service.extend_session('sess_test123')
    
    assert result is True
    mock_redis.expire.assert_called_once_with('session:sess_test123', 3600)

def test_add_chat_message(session_service, mock_redis):
    """测试添加聊天消息"""
    session_id = 'sess_test123'
    existing_data = {
        'session_id': session_id,
        'chat_history': []
    }
    
    mock_redis.get.return_value = json.dumps(existing_data)
    
    result = session_service.add_chat_message(session_id, 'user', 'Hello')
    
    assert result is True
    
    # 验证消息被添加
    call_args = mock_redis.setex.call_args
    updated_data = json.loads(call_args[0][2])
    
    assert len(updated_data['chat_history']) == 1
    assert updated_data['chat_history'][0]['role'] == 'user'
    assert updated_data['chat_history'][0]['message'] == 'Hello'
    assert 'timestamp' in updated_data['chat_history'][0]