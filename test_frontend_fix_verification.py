#!/usr/bin/env python3
"""
验证前端修复 - 测试完整的文件上传和响应流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import tempfile
from io import BytesIO
from flask import Flask
from routes.generation import generation_bp
from services.generation_service import GenerationService
from services.session_service import SessionService
from services.file_service import FileService
from services.ai_service import AIService
from unittest.mock import Mock, patch

def create_test_xml():
    """创建测试XML文件"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="用户登录功能测试">
        <description>
            测试场景：用户登录功能测试
            测试目标：验证用户能够成功登录系统
            前置条件：用户已注册账号
            测试步骤：
            1. 打开登录页面
            2. 输入用户名和密码
            3. 点击登录按钮
            预期结果：成功跳转到用户仪表板页面
        </description>
    </testcase>
</testcases>"""
    return xml_content.encode('utf-8')

def test_complete_flow():
    """测试完整的文件上传和响应流程"""
    
    print("🧪 测试完整的文件上传和响应流程...")
    
    # 创建Flask应用
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['ALLOWED_EXTENSIONS'] = {'.xml'}
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['AI_SERVICE_CONFIG'] = {'mock_mode': False}
    
    # 模拟Redis
    mock_redis = Mock()
    app.redis = mock_redis
    
    app.register_blueprint(generation_bp, url_prefix='/api/generation')
    
    with app.test_client() as client:
        # 模拟Dify成功响应
        mock_dify_response = {
            'success': True,
            'reply': '我已经收到了您的用例文件。为了生成更准确的测试用例，请问：1. 这个系统主要的用户群体是谁？2. 是否有特殊的安全性要求？',
            'conversation_id': 'test_conv_123'
        }
        
        with patch('services.ai_service.AIService.chat_with_agent') as mock_chat:
            mock_chat.return_value = mock_dify_response
            
            # 创建测试文件
            xml_data = create_test_xml()
            
            # 发送文件上传请求
            response = client.post('/api/generation/start', 
                                 data={
                                     'case_template': (BytesIO(xml_data), 'test_case.xml'),
                                     'config': json.dumps({'api_version': 'v1.0'})
                                 },
                                 content_type='multipart/form-data')
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"📋 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # 验证关键字段
                required_fields = ['success', 'session_id', 'message']
                success_checks = []
                
                for field in required_fields:
                    if field in data:
                        success_checks.append(f"✅ {field}: {data[field]}")
                    else:
                        success_checks.append(f"❌ 缺少字段: {field}")
                
                # 检查auto_chat_started字段
                if data.get('auto_chat_started'):
                    success_checks.append("✅ auto_chat_started: True")
                    
                    # 检查消息内容
                    message = data.get('message', '')
                    if '用户群体' in message and '安全性要求' in message:
                        success_checks.append("✅ 消息包含Dify的真实回复")
                    else:
                        success_checks.append(f"❌ 消息内容异常: {message[:50]}...")
                    
                    # 检查其他字段
                    if 'initial_analysis' in data:
                        success_checks.append("✅ initial_analysis字段存在")
                    else:
                        success_checks.append("❌ 缺少initial_analysis字段")
                        
                    if 'extracted_content' in data:
                        success_checks.append("✅ extracted_content字段存在")
                    else:
                        success_checks.append("❌ 缺少extracted_content字段")
                        
                else:
                    success_checks.append("❌ auto_chat_started字段缺失或为False")
                
                print("\n🔍 验证结果:")
                for check in success_checks:
                    print(f"  {check}")
                
                # 判断是否全部成功
                failed_checks = [check for check in success_checks if check.startswith("❌")]
                if not failed_checks:
                    print("\n🎉 所有验证通过！前端修复成功")
                    return True
                else:
                    print(f"\n❌ 有 {len(failed_checks)} 项验证失败")
                    return False
                    
            else:
                error_data = response.get_json() if response.is_json else response.get_data(as_text=True)
                print(f"❌ 请求失败: {error_data}")
                return False

def main():
    """主测试函数"""
    print("🚀 开始验证前端修复...")
    
    try:
        success = test_complete_flow()
        
        if success:
            print("\n🎉 前端修复验证成功！")
            print("\n📝 修复内容:")
            print("- ✅ 修复了routes/generation.py中的响应传递问题")
            print("- ✅ 现在会正确传递auto_chat_started标志")
            print("- ✅ 现在会传递Dify的真实回复消息")
            print("- ✅ 现在会传递所有必要的分析字段")
            print("\n🔧 用户体验改进:")
            print("- 文件上传后立即看到Dify的分析和问题")
            print("- 不再显示Mock消息")
            print("- 可以正常进行多轮对话")
            print("- 对话流程更加自然")
        else:
            print("\n❌ 前端修复验证失败，需要进一步检查")
            
    except Exception as e:
        print(f"❌ 验证异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()