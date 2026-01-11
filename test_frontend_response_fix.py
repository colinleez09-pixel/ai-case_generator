#!/usr/bin/env python3
"""
测试前端响应修复 - 验证路由是否正确传递自动分析结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from unittest.mock import Mock, patch
from routes.generation import generation_bp
from flask import Flask

def test_route_response_structure():
    """测试路由响应结构是否包含所有必要字段"""
    
    print("🧪 测试路由响应结构...")
    
    # 模拟GenerationService返回的完整结果
    mock_result = {
        'success': True,
        'session_id': 'test_session_123',
        'message': 'AI分析完成，请继续对话',  # 这是Dify的真实回复
        'initial_analysis': {
            'template_info': '用例模板分析完成',
            'description': '测试用例内容'
        },
        'auto_chat_started': True,
        'files_processed': 1,
        'extracted_content': '完整的用例描述内容'
    }
    
    # 创建Flask应用进行测试
    app = Flask(__name__)
    app.register_blueprint(generation_bp, url_prefix='/api/generation')
    
    with app.test_client() as client:
        with patch('routes.generation.get_services') as mock_get_services:
            # 模拟服务
            mock_generation_service = Mock()
            mock_generation_service.start_generation_task.return_value = mock_result
            mock_get_services.return_value = (mock_generation_service, Mock(), Mock())
            
            # 模拟文件上传
            with patch('routes.generation.validate_files', return_value=[]):
                response = client.post('/api/generation/start', 
                                     data={'config': '{"api_version": "v1.0"}'},
                                     content_type='multipart/form-data')
                
                print(f"📊 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"📋 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 验证关键字段
                    required_fields = ['success', 'session_id', 'message', 'auto_chat_started', 'initial_analysis']
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"❌ 缺少字段: {missing_fields}")
                        return False
                    else:
                        print("✅ 所有必要字段都存在")
                        
                        # 验证消息内容
                        if data['message'] == mock_result['message']:
                            print("✅ Dify消息正确传递")
                        else:
                            print(f"❌ 消息传递错误: 期望 '{mock_result['message']}', 实际 '{data['message']}'")
                            return False
                        
                        # 验证auto_chat_started标志
                        if data['auto_chat_started'] == True:
                            print("✅ auto_chat_started标志正确")
                        else:
                            print("❌ auto_chat_started标志错误")
                            return False
                        
                        return True
                else:
                    print(f"❌ 请求失败: {response.get_data(as_text=True)}")
                    return False

def main():
    """主测试函数"""
    print("🚀 开始测试前端响应修复...")
    
    try:
        success = test_route_response_structure()
        
        if success:
            print("\n🎉 测试通过！路由现在正确传递所有必要字段给前端")
            print("\n📝 修复总结:")
            print("- ✅ 修复了routes/generation.py中的响应结构")
            print("- ✅ 现在会传递auto_chat_started标志")
            print("- ✅ 现在会传递Dify的真实回复消息")
            print("- ✅ 现在会传递initial_analysis和其他必要字段")
            print("\n🔧 前端现在应该能够:")
            print("- 检测到auto_chat_started=True")
            print("- 显示Dify的真实回复消息")
            print("- 正确处理自动分析结果")
        else:
            print("\n❌ 测试失败，需要进一步检查")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()