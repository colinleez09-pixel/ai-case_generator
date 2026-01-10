import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global shared memory store for sessions when Redis is not available
_GLOBAL_MEMORY_STORE = {}

class SessionService:
    """会话管理服务"""
    
    def __init__(self, redis_client, session_timeout=7200):
        """
        初始化会话服务
        
        Args:
            redis_client: Redis客户端实例（可以为None，使用内存存储）
            session_timeout: 会话超时时间（秒），默认2小时
        """
        self.redis = redis_client
        self.session_timeout = session_timeout
        self.session_prefix = "session:"
        
        # 如果Redis不可用，使用全局共享内存存储
        if self.redis is None:
            global _GLOBAL_MEMORY_STORE
            self._memory_store = _GLOBAL_MEMORY_STORE
            logger.warning("Redis不可用，使用内存存储会话数据")
    
    def create_session(self) -> str:
        """
        创建新的生成会话
        
        Returns:
            str: 会话ID
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        session_data = {
            'session_id': session_id,
            'status': 'created',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'files': {},
            'config': {},
            'chat_history': [],
            'analysis_result': {},
            'test_cases': [],
            'generated_file_id': None
        }
        
        try:
            if self.redis:
                # 存储会话数据到Redis
                key = f"{self.session_prefix}{session_id}"
                self.redis.setex(
                    key,
                    self.session_timeout,
                    json.dumps(session_data, ensure_ascii=False)
                )
            else:
                # 存储到内存
                self._memory_store[session_id] = {
                    'data': session_data,
                    'expires_at': time.time() + self.session_timeout
                }
            
            logger.info(f"会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            raise Exception(f"会话创建失败: {str(e)}")
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话数据，如果会话不存在返回None
        """
        try:
            if self.redis:
                key = f"{self.session_prefix}{session_id}"
                data = self.redis.get(key)
                
                if data is None:
                    logger.warning(f"会话不存在或已过期: {session_id}")
                    return None
                
                session_data = json.loads(data)
                logger.debug(f"获取会话数据成功: {session_id}")
                return session_data
            else:
                # 从内存获取
                logger.debug(f"从内存获取会话数据: {session_id}, 当前存储: {list(self._memory_store.keys())}")
                
                if session_id not in self._memory_store:
                    logger.warning(f"会话不存在: {session_id}")
                    return None
                
                session_info = self._memory_store[session_id]
                
                # 检查是否过期
                if time.time() > session_info['expires_at']:
                    del self._memory_store[session_id]
                    logger.warning(f"会话已过期: {session_id}")
                    return None
                
                logger.debug(f"获取会话数据成功: {session_id}")
                return session_info['data']
                
        except json.JSONDecodeError as e:
            logger.error(f"会话数据解析失败: {session_id}, {e}")
            return None
        except Exception as e:
            logger.error(f"获取会话数据失败: {session_id}, {e}")
            return None
    
    def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            data: 要更新的数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取现有数据
            current_data = self.get_session_data(session_id)
            if current_data is None:
                logger.error(f"无法更新不存在的会话: {session_id}")
                return False
            
            # 合并数据
            current_data.update(data)
            current_data['updated_at'] = datetime.utcnow().isoformat()
            
            if self.redis:
                # 保存到Redis
                key = f"{self.session_prefix}{session_id}"
                self.redis.setex(
                    key, 
                    self.session_timeout, 
                    json.dumps(current_data, ensure_ascii=False)
                )
            else:
                # 保存到内存
                self._memory_store[session_id] = {
                    'data': current_data,
                    'expires_at': time.time() + self.session_timeout
                }
            
            logger.debug(f"更新会话数据成功: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新会话数据失败: {session_id}, {e}")
            return False
    
    def extend_session(self, session_id: str) -> bool:
        """
        延长会话有效期
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 延长是否成功
        """
        try:
            if self.redis:
                key = f"{self.session_prefix}{session_id}"
                
                # 检查会话是否存在
                if not self.redis.exists(key):
                    logger.warning(f"尝试延长不存在的会话: {session_id}")
                    return False
                
                # 延长过期时间
                self.redis.expire(key, self.session_timeout)
            else:
                # 内存存储延长
                if session_id not in self._memory_store:
                    logger.warning(f"尝试延长不存在的会话: {session_id}")
                    return False
                
                self._memory_store[session_id]['expires_at'] = time.time() + self.session_timeout
            
            # 更新最后访问时间
            self.update_session_data(session_id, {
                'last_accessed': datetime.utcnow().isoformat()
            })
            
            logger.debug(f"延长会话成功: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"延长会话失败: {session_id}, {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if self.redis:
                key = f"{self.session_prefix}{session_id}"
                result = self.redis.delete(key)
                
                if result > 0:
                    logger.info(f"删除会话成功: {session_id}")
                    return True
                else:
                    logger.warning(f"会话不存在，无法删除: {session_id}")
                    return False
            else:
                # 内存存储删除
                if session_id in self._memory_store:
                    del self._memory_store[session_id]
                    logger.info(f"删除会话成功: {session_id}")
                    return True
                else:
                    logger.warning(f"会话不存在，无法删除: {session_id}")
                    return False
                
        except Exception as e:
            logger.error(f"删除会话失败: {session_id}, {e}")
            return False
    
    def is_session_valid(self, session_id: str) -> bool:
        """
        检查会话是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否有效
        """
        try:
            if self.redis:
                key = f"{self.session_prefix}{session_id}"
                return self.redis.exists(key) > 0
            else:
                # 内存存储检查
                if session_id not in self._memory_store:
                    return False
                
                # 检查是否过期
                if time.time() > self._memory_store[session_id]['expires_at']:
                    del self._memory_store[session_id]
                    return False
                
                return True
        except Exception as e:
            logger.error(f"检查会话有效性失败: {session_id}, {e}")
            return False
    
    def get_session_status(self, session_id: str) -> Optional[str]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 会话状态，如果会话不存在返回None
        """
        session_data = self.get_session_data(session_id)
        if session_data:
            return session_data.get('status')
        return None
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        更新会话状态
        
        Args:
            session_id: 会话ID
            status: 新状态 (created|analyzing|chatting|generating|completed)
            
        Returns:
            bool: 更新是否成功
        """
        return self.update_session_data(session_id, {'status': status})
    
    def add_chat_message(self, session_id: str, role: str, message: str) -> bool:
        """
        添加聊天消息到会话
        
        Args:
            session_id: 会话ID
            role: 消息角色 (user|ai)
            message: 消息内容
            
        Returns:
            bool: 添加是否成功
        """
        try:
            session_data = self.get_session_data(session_id)
            if session_data is None:
                return False
            
            chat_message = {
                'role': role,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            session_data['chat_history'].append(chat_message)
            
            return self.update_session_data(session_id, {
                'chat_history': session_data['chat_history']
            })
            
        except Exception as e:
            logger.error(f"添加聊天消息失败: {session_id}, {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话（Redis会自动处理，这里主要用于统计）
        
        Returns:
            int: 清理的会话数量
        """
        try:
            # 获取所有会话键
            pattern = f"{self.session_prefix}*"
            keys = self.redis.keys(pattern)
            
            # 检查每个键是否仍然存在（Redis自动清理过期键）
            valid_count = 0
            for key in keys:
                if self.redis.exists(key):
                    valid_count += 1
            
            expired_count = len(keys) - valid_count
            if expired_count > 0:
                logger.info(f"发现 {expired_count} 个过期会话已被自动清理")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0