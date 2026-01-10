from flask import jsonify, current_app, request
import logging
import traceback
from datetime import datetime
import uuid

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理400错误 - 请求参数错误"""
        return jsonify({
            'success': False,
            'error': 'bad_request',
            'message': '请求参数错误',
            'details': {
                'code': 'BAD_REQUEST',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """处理401错误 - 未授权"""
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': '未授权访问',
            'details': {
                'code': 'UNAUTHORIZED',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """处理403错误 - 禁止访问"""
        return jsonify({
            'success': False,
            'error': 'forbidden',
            'message': '禁止访问',
            'details': {
                'code': 'FORBIDDEN',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """处理404错误 - 资源不存在"""
        return jsonify({
            'success': False,
            'error': 'not_found',
            'message': '请求的资源不存在',
            'details': {
                'code': 'NOT_FOUND',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """处理405错误 - 方法不允许"""
        return jsonify({
            'success': False,
            'error': 'method_not_allowed',
            'message': '请求方法不允许',
            'details': {
                'code': 'METHOD_NOT_ALLOWED',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        """处理409错误 - 冲突"""
        return jsonify({
            'success': False,
            'error': 'conflict',
            'message': '请求冲突',
            'details': {
                'code': 'CONFLICT',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 409
    
    @app.errorhandler(410)
    def gone(error):
        """处理410错误 - 资源已过期"""
        return jsonify({
            'success': False,
            'error': 'gone',
            'message': '请求的资源已过期',
            'details': {
                'code': 'GONE',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 410
    
    @app.errorhandler(413)
    def payload_too_large(error):
        """处理413错误 - 请求实体过大"""
        return jsonify({
            'success': False,
            'error': 'payload_too_large',
            'message': '上传文件过大',
            'details': {
                'code': 'PAYLOAD_TOO_LARGE',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8],
                'max_size': f"{app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"
            }
        }), 413
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """处理422错误 - 无法处理的实体"""
        return jsonify({
            'success': False,
            'error': 'unprocessable_entity',
            'message': '请求数据格式错误',
            'details': {
                'code': 'UNPROCESSABLE_ENTITY',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """处理500错误 - 服务器内部错误"""
        request_id = str(uuid.uuid4())[:8]
        
        # 记录详细错误日志
        app.logger.error(f"Internal Server Error [Request ID: {request_id}]")
        app.logger.error(f"URL: {request.url}")
        app.logger.error(f"Method: {request.method}")
        app.logger.error(f"Error: {str(error)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'internal_server_error',
            'message': '服务器内部错误',
            'details': {
                'code': 'INTERNAL_SERVER_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': request_id
            }
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """处理503错误 - 服务不可用"""
        return jsonify({
            'success': False,
            'error': 'service_unavailable',
            'message': '服务暂时不可用',
            'details': {
                'code': 'SERVICE_UNAVAILABLE',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 503
    
    @app.errorhandler(504)
    def gateway_timeout(error):
        """处理504错误 - 网关超时"""
        return jsonify({
            'success': False,
            'error': 'gateway_timeout',
            'message': '请求超时',
            'details': {
                'code': 'GATEWAY_TIMEOUT',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), 504

def setup_request_logging(app):
    """设置请求日志记录"""
    
    @app.before_request
    def log_request_info():
        """记录请求信息"""
        if not request.path.startswith('/health'):  # 跳过健康检查日志
            app.logger.info(f"Request: {request.method} {request.path}")
            if request.is_json and request.get_json():
                # 不记录敏感数据
                data = request.get_json()
                safe_data = {k: v for k, v in data.items() if k not in ['password', 'token', 'secret']}
                app.logger.debug(f"Request data: {safe_data}")
    
    @app.after_request
    def log_response_info(response):
        """记录响应信息"""
        if not request.path.startswith('/health'):  # 跳过健康检查日志
            app.logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response

class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or []
        super().__init__(self.message)

class SessionError(Exception):
    """会话错误异常"""
    def __init__(self, message, status_code=404):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileError(Exception):
    """文件错误异常"""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AIServiceError(Exception):
    """AI服务错误异常"""
    def __init__(self, message, status_code=503):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def register_custom_error_handlers(app):
    """注册自定义异常处理器"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """处理验证错误"""
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': error.message,
            'details': {
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8],
                'validation_errors': error.details
            }
        }), 400
    
    @app.errorhandler(SessionError)
    def handle_session_error(error):
        """处理会话错误"""
        return jsonify({
            'success': False,
            'error': 'session_error',
            'message': error.message,
            'details': {
                'code': 'SESSION_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), error.status_code
    
    @app.errorhandler(FileError)
    def handle_file_error(error):
        """处理文件错误"""
        return jsonify({
            'success': False,
            'error': 'file_error',
            'message': error.message,
            'details': {
                'code': 'FILE_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), error.status_code
    
    @app.errorhandler(AIServiceError)
    def handle_ai_service_error(error):
        """处理AI服务错误"""
        return jsonify({
            'success': False,
            'error': 'ai_service_error',
            'message': error.message,
            'details': {
                'code': 'AI_SERVICE_ERROR',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'request_id': str(uuid.uuid4())[:8]
            }
        }), error.status_code