from flask import Blueprint, request, jsonify, current_app, Response
import logging
import json
from services.chat_service import ChatService
from services.session_service import SessionService
from services.ai_service import AIService
from services.streaming_chat_handler import StreamingChatHandler

chat_bp = Blueprint('chat', __name__)

def get_services():
    """获取服务实例"""
    session_service = SessionService(current_app.redis)
    ai_service = AIService(current_app.config['AI_SERVICE_CONFIG'])
    chat_service = ChatService(ai_service, session_service)
    return chat_service, session_service

def get_streaming_handler():
    """获取流式聊天处理器"""
    ai_service = AIService(current_app.config['AI_SERVICE_CONFIG'])
    return StreamingChatHandler(ai_service)

@chat_bp.route('/streaming/support', methods=['GET'])
def check_streaming_support():
    """检查是否支持流式API"""
    try:
        return jsonify({
            'success': True,
            'supported': True,
            'message': '支持流式聊天API'
        })
    except Exception as e:
        current_app.logger.error(f"检查流式API支持失败: {str(e)}")
        return jsonify({
            'success': False,
            'supported': False,
            'message': '流式API不可用'
        }), 500

@chat_bp.route('/stream', methods=['POST'])
def stream_chat():
    """流式聊天端点 - 支持Server-Sent Events"""
    import asyncio
    
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        if not message or not message.strip():
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '消息内容不能为空'
            }), 400
        
        # 获取服务实例
        _, session_service = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 检查会话状态
        current_status = session_data.get('status')
        if current_status not in ['analyzing', 'chatting']:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': f'当前会话状态({current_status})不支持对话'
            }), 409
        
        # 获取流式处理器
        streaming_handler = get_streaming_handler()
        
        def generate_stream():
            """生成SSE流式响应 - 同步包装器"""
            try:
                # 创建新的事件循环来运行异步代码
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # 运行异步生成器
                    async def async_generator():
                        async for chunk in streaming_handler.handle_streaming_chat(session_id, message.strip()):
                            yield chunk
                    
                    # 同步迭代异步生成器
                    async_gen = async_generator()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                            
                finally:
                    loop.close()
                    
            except Exception as e:
                current_app.logger.error(f"流式聊天生成异常: {e}")
                error_chunk = f"data: {json.dumps({'type': 'error', 'data': {'error': 'stream_error', 'message': str(e)}}, ensure_ascii=False)}\n\n"
                yield error_chunk
        
        # 返回SSE响应
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"流式聊天端点异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@chat_bp.route('/send', methods=['POST'])
def send_message():
    """发送聊天消息"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        if not message or not message.strip():
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '消息内容不能为空'
            }), 400
        
        # 获取服务实例
        chat_service, session_service = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 检查会话状态
        current_status = session_data.get('status')
        if current_status not in ['analyzing', 'chatting']:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': f'当前会话状态({current_status})不支持对话'
            }), 409
        
        # 处理聊天消息
        result = chat_service.send_message(session_id, message.strip())
        
        if result['success']:
            response_data = {
                'success': True,
                'message': result['reply'],
                'session_status': result.get('session_status'),
                'ready_to_generate': result.get('ready_to_generate', False)
            }
            
            # 如果有分析结果，包含在响应中
            if 'analysis_result' in result:
                response_data['analysis_result'] = result['analysis_result']
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"处理聊天消息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@chat_bp.route('/history', methods=['GET'])
def get_chat_history():
    """获取聊天历史"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        # 获取服务实例
        chat_service, session_service = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 获取聊天历史
        chat_history = chat_service.get_chat_history(session_id)
        
        return jsonify({
            'success': True,
            'chat_history': chat_history,
            'session_status': session_data.get('status')
        })
        
    except Exception as e:
        current_app.logger.error(f"获取聊天历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@chat_bp.route('/clear', methods=['POST'])
def clear_chat_history():
    """清空聊天历史"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        session_id = data['session_id']
        
        # 获取服务实例
        chat_service, session_service = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 清空聊天历史
        result = chat_service.clear_chat_history(session_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '聊天历史已清空'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"清空聊天历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500