import re
import os
from werkzeug.utils import secure_filename
from flask import current_app
import xml.etree.ElementTree as ET
from utils.error_handlers import ValidationError, FileError

def validate_session_id(session_id):
    """验证会话ID格式"""
    if not session_id:
        raise ValidationError("会话ID不能为空")
    
    if not isinstance(session_id, str):
        raise ValidationError("会话ID必须是字符串")
    
    # 会话ID格式: sess_xxxxxxxx (sess_前缀 + 8位字符)
    if not re.match(r'^sess_[a-zA-Z0-9]{8}$', session_id):
        raise ValidationError("会话ID格式不正确")
    
    return True

def validate_file_id(file_id):
    """验证文件ID格式"""
    if not file_id:
        raise ValidationError("文件ID不能为空")
    
    if not isinstance(file_id, str):
        raise ValidationError("文件ID必须是字符串")
    
    # 文件ID格式: file_xxxxxxxx (file_前缀 + 8位字符)
    if not re.match(r'^file_[a-zA-Z0-9]{8}$', file_id):
        raise ValidationError("文件ID格式不正确")
    
    return True

def validate_message(message):
    """验证聊天消息"""
    if not message:
        raise ValidationError("消息内容不能为空")
    
    if not isinstance(message, str):
        raise ValidationError("消息内容必须是字符串")
    
    message = message.strip()
    if not message:
        raise ValidationError("消息内容不能为空")
    
    if len(message) > 5000:
        raise ValidationError("消息内容过长，最多5000个字符")
    
    # 检查是否包含恶意内容
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',  # JavaScript协议
        r'on\w+\s*=',  # 事件处理器
        r'<iframe[^>]*>.*?</iframe>',  # iframe
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
            raise ValidationError("消息内容包含不安全的内容")
    
    return message

def validate_uploaded_file(file, file_type):
    """验证上传的文件"""
    if not file:
        raise FileError(f"文件类型 {file_type} 为空")
    
    if file.filename == '':
        raise FileError(f"文件类型 {file_type} 没有选择文件")
    
    # 验证文件名安全性
    filename = secure_filename(file.filename)
    if not filename:
        raise FileError(f"文件名 {file.filename} 不安全")
    
    # 验证文件扩展名
    if not filename.lower().endswith('.xml'):
        raise FileError(f"文件 {filename} 格式不正确，只支持XML格式")
    
    # 验证文件大小
    file.seek(0, 2)  # 移动到文件末尾
    size = file.tell()
    file.seek(0)  # 重置到开头
    
    max_size = current_app.config['MAX_CONTENT_LENGTH']
    if size > max_size:
        raise FileError(f"文件 {filename} 大小({size}字节)超过限制({max_size}字节)")
    
    if size == 0:
        raise FileError(f"文件 {filename} 为空")
    
    return filename

def validate_xml_content(file_content, file_type):
    """验证XML文件内容"""
    try:
        root = ET.fromstring(file_content)
    except ET.ParseError as e:
        raise FileError(f"XML文件解析失败: {str(e)}")
    
    # 根据文件类型验证XML结构
    if file_type == 'case_template':
        validate_case_template_xml(root)
    elif file_type == 'history_case':
        validate_history_case_xml(root)
    elif file_type == 'aw_template':
        validate_aw_template_xml(root)
    
    return True

def validate_case_template_xml(root):
    """验证用例模板XML结构"""
    if root.tag != 'testcases':
        raise FileError("用例模板XML根元素必须是 <testcases>")
    
    # 检查是否有测试用例
    testcases = root.findall('testcase')
    if not testcases:
        raise FileError("用例模板XML必须包含至少一个 <testcase> 元素")
    
    # 验证每个测试用例的基本结构
    for i, testcase in enumerate(testcases):
        case_id = testcase.get('id')
        if not case_id:
            raise FileError(f"第{i+1}个测试用例缺少id属性")
        
        # 检查必要的子元素
        required_elements = ['name', 'preconditions', 'steps', 'expectedresults']
        for element in required_elements:
            if testcase.find(element) is None:
                raise FileError(f"测试用例 {case_id} 缺少 <{element}> 元素")

def validate_history_case_xml(root):
    """验证历史用例XML结构"""
    if root.tag != 'testcases':
        raise FileError("历史用例XML根元素必须是 <testcases>")
    
    # 历史用例可以为空，但如果有用例则需要验证结构
    testcases = root.findall('testcase')
    for i, testcase in enumerate(testcases):
        case_id = testcase.get('id')
        if not case_id:
            raise FileError(f"第{i+1}个历史用例缺少id属性")

def validate_aw_template_xml(root):
    """验证AW模板XML结构"""
    # AW模板的验证规则可以根据具体需求调整
    if root.tag not in ['testcases', 'template', 'aw']:
        raise FileError("AW模板XML根元素格式不正确")

def validate_test_cases_data(test_cases):
    """验证测试用例数据结构"""
    if not isinstance(test_cases, list):
        raise ValidationError("测试用例数据必须是数组")
    
    if not test_cases:
        raise ValidationError("测试用例数据不能为空")
    
    for i, test_case in enumerate(test_cases):
        if not isinstance(test_case, dict):
            raise ValidationError(f"第{i+1}个测试用例数据格式不正确")
        
        # 验证必要字段
        required_fields = ['id', 'name', 'preconditions', 'steps', 'expectedResults']
        for field in required_fields:
            if field not in test_case:
                raise ValidationError(f"第{i+1}个测试用例缺少字段: {field}")
        
        # 验证ID格式
        case_id = test_case['id']
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValidationError(f"第{i+1}个测试用例ID格式不正确")
        
        # 验证名称
        case_name = test_case['name']
        if not isinstance(case_name, str) or not case_name.strip():
            raise ValidationError(f"测试用例 {case_id} 名称不能为空")
        
        # 验证数组字段
        for field in ['preconditions', 'steps', 'expectedResults']:
            if not isinstance(test_case[field], list):
                raise ValidationError(f"测试用例 {case_id} 的 {field} 必须是数组")

def validate_api_version(api_version):
    """验证API版本"""
    if not api_version:
        raise ValidationError("API版本不能为空")
    
    if not isinstance(api_version, str):
        raise ValidationError("API版本必须是字符串")
    
    # API版本格式: v1.0, v2.0 等
    if not re.match(r'^v\d+\.\d+$', api_version):
        raise ValidationError("API版本格式不正确，应为 vX.Y 格式")
    
    return True

def sanitize_filename(filename):
    """清理文件名，确保安全"""
    if not filename:
        return None
    
    # 使用werkzeug的secure_filename
    safe_filename = secure_filename(filename)
    
    # 额外的安全检查
    if not safe_filename:
        return None
    
    # 限制文件名长度
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:250] + ext
    
    return safe_filename

def validate_config_data(config_data):
    """验证配置数据"""
    if not isinstance(config_data, dict):
        raise ValidationError("配置数据必须是对象")
    
    # 验证API版本
    if 'api_version' in config_data:
        validate_api_version(config_data['api_version'])
    
    # 验证其他配置项
    allowed_keys = ['api_version', 'timeout', 'max_retries', 'custom_settings']
    for key in config_data:
        if key not in allowed_keys:
            raise ValidationError(f"不支持的配置项: {key}")
    
    return True