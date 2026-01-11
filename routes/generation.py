from flask import Blueprint, request, jsonify, Response, current_app, send_file
from werkzeug.utils import secure_filename
import os
import json
import logging
from services.generation_service import GenerationService
from services.session_service import SessionService
from services.file_service import FileService
from services.ai_service import AIService

generation_bp = Blueprint('generation', __name__)

def get_services():
    """获取服务实例"""
    session_service = SessionService(current_app.redis)
    file_service = FileService(current_app.config['UPLOAD_FOLDER'])
    ai_service = AIService(current_app.config['AI_SERVICE_CONFIG'])
    generation_service = GenerationService(file_service, session_service, ai_service)
    return generation_service, session_service, file_service

def validate_files(files):
    """验证上传的文件"""
    errors = []
    
    if not files:
        errors.append("没有上传文件")
        return errors
    
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    for file_type, file in files.items():
        if not file or file.filename == '':
            errors.append(f"文件类型 {file_type} 为空")
            continue
            
        if not file.filename.lower().endswith('.xml'):
            errors.append(f"文件 {file.filename} 格式不正确，只支持XML格式")
            
        # 检查文件大小
        file.seek(0, 2)  # 移动到文件末尾
        size = file.tell()
        file.seek(0)  # 重置到开头
        
        if size > current_app.config['MAX_CONTENT_LENGTH']:
            errors.append(f"文件 {file.filename} 大小超过限制")
    
    return errors

@generation_bp.route('/create-session', methods=['POST'])
def create_session():
    """创建新的生成会话"""
    try:
        # 获取服务实例
        _, session_service, _ = get_services()
        
        # 创建新会话
        session_id = session_service.create_session()
        
        # 更新会话状态为chatting，使其可以进行对话
        session_service.update_session_data(session_id, {
            'status': 'chatting'
        })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '会话创建成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"创建会话失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@generation_bp.route('/start', methods=['POST'])
def start_generation():
    """开始生成任务 - 处理文件上传和配置"""
    try:
        # 获取上传的文件
        files = {}
        for file_type in ['history_case', 'case_template', 'aw_template']:
            if file_type in request.files:
                file = request.files[file_type]
                if file and file.filename != '':
                    files[file_type] = file
        
        # 验证至少有一个必需文件
        if 'case_template' not in files:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少必需的用例模板文件'
            }), 400
        
        # 验证文件
        validation_errors = validate_files(files)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '文件验证失败',
                'details': validation_errors
            }), 400
        
        # 获取配置参数
        config_data = {}
        if 'config' in request.form:
            try:
                config_data = json.loads(request.form['config'])
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'validation_error',
                    'message': '配置参数格式错误'
                }), 400
        
        # 获取服务实例
        generation_service, _, _ = get_services()
        
        # 启动生成任务
        result = generation_service.start_generation_task(files, config_data)
        
        if result['success']:
            response_data = {
                'success': True,
                'session_id': result['session_id'],
                'message': result.get('message', '任务启动成功'),
                'analysis_result': result.get('analysis_result')
            }
            
            # 传递自动分析相关的字段
            if result.get('auto_chat_started'):
                response_data['auto_chat_started'] = True
                response_data['initial_analysis'] = result.get('initial_analysis', {})
                response_data['files_processed'] = result.get('files_processed', 0)
                response_data['extracted_content'] = result.get('extracted_content', '')
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"启动生成任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@generation_bp.route('/generate', methods=['POST'])
def generate_test_cases():
    """生成测试用例 - 流式响应"""
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
        generation_service, session_service, _ = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 检查会话状态
        if session_data.get('status') != 'ready_to_generate':
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话状态不正确，请先完成对话交互'
            }), 409
        
        # 生成流式响应
        def generate_stream():
            try:
                for chunk in generation_service.generate_test_cases_stream(session_id):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                current_app.logger.error(f"生成测试用例失败: {str(e)}")
                error_chunk = {
                    'type': 'error',
                    'error': 'generation_error',
                    'message': '生成过程中发生错误'
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return Response(
            generate_stream(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"生成测试用例请求处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@generation_bp.route('/finalize', methods=['POST'])
def finalize_generation():
    """确认并生成最终文件"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        session_id = data['session_id']
        test_cases = data.get('test_cases', [])
        
        # 获取服务实例
        generation_service, session_service, _ = get_services()
        
        # 验证会话
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 确认生成
        result = generation_service.finalize_test_cases(session_id, test_cases)
        
        if result['success']:
            return jsonify({
                'success': True,
                'file_id': result['file_id'],
                'message': '测试用例生成完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"确认生成失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@generation_bp.route('/download', methods=['GET'])
def download_file():
    """下载用例文件"""
    try:
        session_id = request.args.get('session_id')
        file_id = request.args.get('file_id')
        
        if not session_id or not file_id:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少必要参数'
            }), 400
        
        # 获取服务实例
        _, session_service, file_service = get_services()
        
        # 验证会话和权限
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        # 验证文件ID
        if session_data.get('generated_file_id') != file_id:
            return jsonify({
                'success': False,
                'error': 'permission_error',
                'message': '无权限下载该文件'
            }), 403
        
        # 获取文件路径
        file_path = session_data.get('generated_file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'file_error',
                'message': '文件路径不存在'
            }), 404
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'file_error',
                'message': '文件不存在'
            }), 404
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"test_cases_{file_id}.xml",
            mimetype='application/xml'
        )
        
    except Exception as e:
        current_app.logger.error(f"文件下载失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@generation_bp.route('/status', methods=['GET'])
def get_generation_status():
    """获取生成任务状态"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': '缺少会话ID'
            }), 400
        
        # 获取服务实例
        _, session_service, _ = get_services()
        
        # 获取会话数据
        session_data = session_service.get_session_data(session_id)
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'session_error',
                'message': '会话不存在或已过期'
            }), 404
        
        return jsonify({
            'success': True,
            'status': session_data.get('status', 'unknown'),
            'created_at': session_data.get('created_at'),
            'updated_at': session_data.get('updated_at')
        })
        
    except Exception as e:
        current_app.logger.error(f"获取状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500