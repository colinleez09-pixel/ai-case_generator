from flask import Flask
from flask_cors import CORS
import redis
import os
import logging
from config import config
from utils.error_handlers import (
    register_error_handlers, 
    register_custom_error_handlers, 
    setup_request_logging
)

# 移除Dify连接补丁，保持代理设置
print("🔧 使用正常代理设置连接Dify")

def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 启用CORS支持
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:5000'])
    
    # 配置日志
    logging.basicConfig(level=getattr(logging, app.config['LOG_LEVEL']))
    
    # 初始化Redis连接
    try:
        app.redis = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            decode_responses=True
        )
        # 测试Redis连接
        app.redis.ping()
        app.logger.info("Redis连接成功")
    except redis.ConnectionError:
        app.logger.warning("Redis连接失败，某些功能可能不可用")
        app.redis = None
    
    # 创建上传目录
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # 注册错误处理器
    register_error_handlers(app)
    register_custom_error_handlers(app)
    setup_request_logging(app)
    
    # 注册蓝图
    from routes.generation import generation_bp
    from routes.chat import chat_bp
    from routes.config import config_bp
    
    app.register_blueprint(generation_bp, url_prefix='/api/generation')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'redis': app.redis is not None}
    
    # 主页路由
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    # 测试页面路由
    @app.route('/test')
    def test_page():
        from flask import render_template
        return render_template('test.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)