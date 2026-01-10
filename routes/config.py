from flask import Blueprint, jsonify, current_app
import logging
from services.config_service import ConfigService

config_bp = Blueprint('config', __name__)

def get_config_service():
    """获取配置服务实例"""
    return ConfigService()

@config_bp.route('/api-versions', methods=['GET'])
def get_api_versions():
    """获取API版本列表"""
    try:
        config_service = get_config_service()
        api_versions = config_service.get_api_versions()
        
        return jsonify({
            'success': True,
            'api_versions': api_versions
        })
        
    except Exception as e:
        current_app.logger.error(f"获取API版本列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@config_bp.route('/preset-steps', methods=['GET'])
def get_preset_steps():
    """获取预设步骤列表"""
    try:
        config_service = get_config_service()
        preset_steps = config_service.get_preset_steps()
        
        return jsonify({
            'success': True,
            'preset_steps': preset_steps
        })
        
    except Exception as e:
        current_app.logger.error(f"获取预设步骤列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@config_bp.route('/preset-components', methods=['GET'])
def get_preset_components():
    """获取预设组件列表"""
    try:
        config_service = get_config_service()
        preset_components = config_service.get_preset_components()
        
        return jsonify({
            'success': True,
            'preset_components': preset_components
        })
        
    except Exception as e:
        current_app.logger.error(f"获取预设组件列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@config_bp.route('/all', methods=['GET'])
def get_all_config():
    """获取所有配置数据"""
    try:
        config_service = get_config_service()
        
        return jsonify({
            'success': True,
            'config': {
                'api_versions': config_service.get_api_versions(),
                'preset_steps': config_service.get_preset_steps(),
                'preset_components': config_service.get_preset_components()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取配置数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500

@config_bp.route('/health', methods=['GET'])
def config_health_check():
    """配置服务健康检查"""
    try:
        config_service = get_config_service()
        
        # 简单验证配置服务是否正常
        api_versions = config_service.get_api_versions()
        preset_steps = config_service.get_preset_steps()
        preset_components = config_service.get_preset_components()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'stats': {
                'api_versions_count': len(api_versions),
                'preset_steps_count': len(preset_steps),
                'preset_components_count': len(preset_components)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"配置服务健康检查失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': '配置服务不可用'
        }), 500