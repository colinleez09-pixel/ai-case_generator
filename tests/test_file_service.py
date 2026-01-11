import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch
from werkzeug.datastructures import FileStorage
from io import BytesIO
from datetime import datetime

from services.file_service import FileService


class TestFileService:
    """FileService单元测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_service(self, temp_dir):
        """创建FileService实例"""
        return FileService(temp_dir)
    
    @pytest.fixture
    def sample_xml_content(self):
        """示例XML内容"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="登录测试">
        <preconditions>
            <precondition name="用户已注册">
                <component type="api" name="检查用户存在">
                    <params>
                        <param name="method">GET</param>
                        <param name="url">/api/users/check</param>
                    </params>
                </component>
            </precondition>
        </preconditions>
        <steps>
            <step name="打开登录页面">
                <component type="api" name="获取登录页">
                    <params>
                        <param name="method">GET</param>
                        <param name="url">/login</param>
                    </params>
                </component>
            </step>
        </steps>
        <expectedResults>
            <expectedResult name="登录成功">
                <component type="assert" name="验证跳转">
                    <params>
                        <param name="type">equals</param>
                        <param name="expected">/dashboard</param>
                    </params>
                </component>
            </expectedResult>
        </expectedResults>
    </testcase>
</testcases>'''
    
    @pytest.fixture
    def invalid_xml_content(self):
        """无效XML内容"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="测试">
        <unclosed_tag>
    </testcase>
</testcases>'''
    
    @pytest.fixture
    def mock_file_storage(self, sample_xml_content):
        """创建模拟的FileStorage对象"""
        def create_mock_file(filename, content):
            mock_file = Mock(spec=FileStorage)
            mock_file.filename = filename
            mock_file.save = Mock()
            # 模拟保存文件的行为
            def save_side_effect(path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            mock_file.save.side_effect = save_side_effect
            return mock_file
        return create_mock_file
    
    def test_init_creates_upload_folder(self, temp_dir):
        """测试初始化时创建上传目录"""
        upload_dir = os.path.join(temp_dir, 'uploads')
        assert not os.path.exists(upload_dir)
        
        FileService(upload_dir)
        assert os.path.exists(upload_dir)
    
    def test_is_allowed_file_valid_extensions(self, file_service):
        """测试允许的文件扩展名"""
        assert file_service.is_allowed_file('test.xml') is True
        assert file_service.is_allowed_file('test.XML') is True
        assert file_service.is_allowed_file('test.txt') is False
        assert file_service.is_allowed_file('test') is False
        assert file_service.is_allowed_file('test.') is False
    
    def test_save_uploaded_file_success(self, file_service, mock_file_storage, sample_xml_content):
        """测试成功保存上传文件"""
        mock_file = mock_file_storage('test.xml', sample_xml_content)
        session_id = 'test_session_123'
        
        result = file_service.save_uploaded_file(mock_file, session_id, 'template')
        
        # 验证返回结果
        assert 'file_id' in result
        assert result['original_name'] == 'test.xml'
        assert result['file_type'] == 'template'
        assert result['file_size'] > 0
        assert 'upload_time' in result
        
        # 验证文件确实被保存
        assert os.path.exists(result['file_path'])
        
        # 验证会话目录被创建
        session_dir = os.path.join(file_service.upload_folder, session_id)
        assert os.path.exists(session_dir)
    
    def test_save_uploaded_file_no_file(self, file_service):
        """测试没有文件时的错误处理"""
        with pytest.raises(ValueError, match="没有选择文件"):
            file_service.save_uploaded_file(None, 'session_123', 'template')
    
    def test_save_uploaded_file_empty_filename(self, file_service):
        """测试空文件名的错误处理"""
        mock_file = Mock(spec=FileStorage)
        mock_file.filename = ''
        
        with pytest.raises(ValueError, match="没有选择文件"):
            file_service.save_uploaded_file(mock_file, 'session_123', 'template')
    
    def test_save_uploaded_file_invalid_extension(self, file_service):
        """测试不支持的文件扩展名"""
        mock_file = Mock(spec=FileStorage)
        mock_file.filename = 'test.txt'
        
        with pytest.raises(ValueError, match="不支持的文件类型"):
            file_service.save_uploaded_file(mock_file, 'session_123', 'template')
    
    def test_save_uploaded_file_invalid_xml(self, file_service, mock_file_storage, invalid_xml_content):
        """测试无效XML文件的处理"""
        mock_file = mock_file_storage('invalid.xml', invalid_xml_content)
        
        with pytest.raises(ValueError, match="XML文件格式错误"):
            file_service.save_uploaded_file(mock_file, 'session_123', 'template')
    
    def test_parse_xml_file_success(self, file_service, temp_dir, sample_xml_content):
        """测试成功解析XML文件"""
        # 创建临时XML文件
        xml_file = os.path.join(temp_dir, 'test.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(sample_xml_content)
        
        result = file_service.parse_xml_file(xml_file)
        
        # 验证基本信息
        assert result['root_tag'] == 'testcases'
        assert result['total_elements'] > 0
        assert 'structure' in result
        
        # 验证测试用例特殊信息
        assert result['test_case_count'] == 1
        assert len(result['test_cases']) == 1
        assert result['test_cases'][0]['id'] == 'TC001'
        assert result['test_cases'][0]['name'] == '登录测试'
    
    def test_parse_xml_file_invalid_format(self, file_service, temp_dir, invalid_xml_content):
        """测试解析无效XML文件"""
        xml_file = os.path.join(temp_dir, 'invalid.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(invalid_xml_content)
        
        with pytest.raises(ValueError, match="XML格式错误"):
            file_service.parse_xml_file(xml_file)
    
    def test_parse_xml_file_not_exists(self, file_service):
        """测试解析不存在的文件"""
        with pytest.raises(Exception):
            file_service.parse_xml_file('/nonexistent/file.xml')
    
    def test_generate_xml_output_success(self, file_service):
        """测试生成XML输出"""
        test_cases = [
            {
                'id': 'TC001',
                'name': '登录测试',
                'preconditions': [
                    {
                        'name': '用户已注册',
                        'components': [
                            {
                                'type': 'api',
                                'name': '检查用户存在',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/users/check'
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'name': '打开登录页面',
                        'components': [
                            {
                                'type': 'api',
                                'name': '获取登录页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/login'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'name': '登录成功',
                        'components': [
                            {
                                'type': 'assert',
                                'name': '验证跳转',
                                'params': {
                                    'type': 'equals',
                                    'expected': '/dashboard'
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        xml_content = file_service.generate_xml_output(test_cases)
        
        # 验证XML格式正确
        assert xml_content.startswith('<?xml version="1.0" ?>')
        assert '<testcases' in xml_content
        assert 'generated_at=' in xml_content
        assert 'count="1"' in xml_content
        assert '<testcase id="TC001"' in xml_content
        assert '<preconditions>' in xml_content
        assert '<steps>' in xml_content
        assert '<expectedResults>' in xml_content
    
    def test_generate_xml_output_empty_list(self, file_service):
        """测试生成空测试用例列表的XML"""
        xml_content = file_service.generate_xml_output([])
        
        assert xml_content.startswith('<?xml version="1.0" ?>')
        assert '<testcases' in xml_content
        assert 'count="0"' in xml_content
    
    def test_save_generated_file_success(self, file_service):
        """测试保存生成的文件"""
        session_id = 'test_session_123'
        xml_content = '<?xml version="1.0"?><testcases></testcases>'
        
        result = file_service.save_generated_file(session_id, xml_content)
        
        # 验证返回结果
        assert 'file_id' in result
        assert result['filename'].startswith(f'{session_id}_generated_')
        assert result['filename'].endswith('.xml')
        assert result['file_size'] > 0
        assert 'generated_at' in result
        
        # 验证文件确实被保存
        assert os.path.exists(result['file_path'])
        
        # 验证文件内容
        with open(result['file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == xml_content
    
    def test_get_file_content_success(self, file_service, temp_dir):
        """测试获取文件内容"""
        test_content = b'test file content'
        test_file = os.path.join(temp_dir, 'test.txt')
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        content = file_service.get_file_content(test_file)
        assert content == test_content
    
    def test_get_file_content_not_exists(self, file_service):
        """测试获取不存在文件的内容"""
        with pytest.raises(FileNotFoundError):
            file_service.get_file_content('/nonexistent/file.txt')
    
    def test_cleanup_session_files_success(self, file_service):
        """测试清理会话文件"""
        session_id = 'test_session_123'
        
        # 创建会话目录和文件
        session_dir = os.path.join(file_service.upload_folder, session_id)
        os.makedirs(session_dir)
        test_file = os.path.join(session_dir, 'test.xml')
        with open(test_file, 'w') as f:
            f.write('test')
        
        assert os.path.exists(session_dir)
        assert os.path.exists(test_file)
        
        # 清理文件
        result = file_service.cleanup_session_files(session_id)
        
        assert result is True
        assert not os.path.exists(session_dir)
        assert not os.path.exists(test_file)
    
    def test_cleanup_session_files_not_exists(self, file_service):
        """测试清理不存在的会话文件"""
        result = file_service.cleanup_session_files('nonexistent_session')
        assert result is False
    
    def test_get_file_info_success(self, file_service):
        """测试获取文件信息"""
        session_id = 'test_session_123'
        file_id = 'template_abc123'
        
        # 创建测试文件
        session_dir = os.path.join(file_service.upload_folder, session_id)
        os.makedirs(session_dir)
        filename = f'{session_id}_{file_id}_test.xml'
        test_file = os.path.join(session_dir, filename)
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = file_service.get_file_info(session_id, file_id)
        
        assert result is not None
        assert result['file_id'] == file_id
        assert result['filename'] == filename
        assert result['file_path'] == test_file
        assert result['file_size'] > 0
        assert 'modified_time' in result
    
    def test_get_file_info_not_exists(self, file_service):
        """测试获取不存在文件的信息"""
        result = file_service.get_file_info('nonexistent_session', 'nonexistent_file')
        assert result is None
    
    def test_get_file_info_session_not_exists(self, file_service):
        """测试获取不存在会话的文件信息"""
        result = file_service.get_file_info('nonexistent_session', 'some_file')
        assert result is None
    
    def test_extract_test_case_description_success(self, file_service, temp_dir):
        """测试成功提取测试用例描述"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <precondition>CBS系统运行正常</precondition>
    <precondition>修改系统变量SYS_abc的值为12</precondition>
    <step>进行调账，调减20元</step>
    <step>验证账户余额</step>
    <expected>调账成功</expected>
    <expected>account_balance表amount字段值为80</expected>
</testcase>'''
        
        # 创建临时XML文件
        xml_file = os.path.join(temp_dir, 'test_extract.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        result = file_service.extract_test_case_description(xml_file)
        
        # 验证格式化输出
        assert '【预置条件】' in result
        assert '1. CBS系统运行正常' in result
        assert '2. 修改系统变量SYS_abc的值为12' in result
        assert '【测试步骤】' in result
        assert '1. 进行调账，调减20元' in result
        assert '2. 验证账户余额' in result
        assert '【预期结果】' in result
        assert '1. 调账成功' in result
        assert '2. account_balance表amount字段值为80' in result
    
    def test_extract_test_case_description_nested_structure(self, file_service, temp_dir):
        """测试提取嵌套结构的测试用例描述"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001">
        <preconditions>
            <precondition>系统初始化完成</precondition>
            <precondition>用户已登录</precondition>
        </preconditions>
        <steps>
            <step>打开页面</step>
            <step>输入数据</step>
        </steps>
        <expectedResults>
            <expectedResult>页面正常显示</expectedResult>
            <expectedResult>数据保存成功</expectedResult>
        </expectedResults>
    </testcase>
</testcases>'''
        
        xml_file = os.path.join(temp_dir, 'test_nested.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        result = file_service.extract_test_case_description(xml_file)
        
        assert '【预置条件】' in result
        assert '1. 系统初始化完成' in result
        assert '2. 用户已登录' in result
        assert '【测试步骤】' in result
        assert '1. 打开页面' in result
        assert '2. 输入数据' in result
        assert '【预期结果】' in result
        assert '1. 页面正常显示' in result
        assert '2. 数据保存成功' in result
    
    def test_extract_test_case_description_chinese_tags(self, file_service, temp_dir):
        """测试提取中文标签的测试用例描述"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<测试用例>
    <前置条件>环境准备完成</前置条件>
    <测试步骤>执行操作</测试步骤>
    <预期结果>操作成功</预期结果>
</测试用例>'''
        
        xml_file = os.path.join(temp_dir, 'test_chinese.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        result = file_service.extract_test_case_description(xml_file)
        
        assert '【预置条件】' in result
        assert '1. 环境准备完成' in result
        assert '【测试步骤】' in result
        assert '1. 执行操作' in result
        assert '【预期结果】' in result
        assert '1. 操作成功' in result
    
    def test_extract_test_case_description_multiple_testcases(self, file_service, temp_dir):
        """测试提取多个测试用例的描述"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001">
        <precondition>前置条件1</precondition>
        <step>步骤1</step>
        <expected>结果1</expected>
    </testcase>
    <testcase id="TC002">
        <precondition>前置条件2</precondition>
        <step>步骤2</step>
        <expected>结果2</expected>
    </testcase>
</testcases>'''
        
        xml_file = os.path.join(temp_dir, 'test_multiple.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        result = file_service.extract_test_case_description(xml_file)
        
        # 应该合并所有测试用例的内容
        assert '【预置条件】' in result
        assert '前置条件1' in result
        assert '前置条件2' in result
        assert '【测试步骤】' in result
        assert '步骤1' in result
        assert '步骤2' in result
        assert '【预期结果】' in result
        assert '结果1' in result
        assert '结果2' in result
    
    def test_extract_test_case_description_empty_content(self, file_service, temp_dir):
        """测试提取空内容时返回默认模板"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <other_tag>其他内容</other_tag>
</testcase>'''
        
        xml_file = os.path.join(temp_dir, 'test_empty.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        result = file_service.extract_test_case_description(xml_file)
        
        # 应该返回默认模板
        assert '【预置条件】' in result
        assert 'CBS系统运行正常' in result
        assert '【测试步骤】' in result
        assert '进行调账，调减20元' in result
        assert '【预期结果】' in result
        assert '调账成功' in result
    
    def test_extract_test_case_description_invalid_xml(self, file_service, temp_dir):
        """测试无效XML文件时返回默认模板"""
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<testcase>
    <unclosed_tag>
</testcase>'''
        
        xml_file = os.path.join(temp_dir, 'test_invalid.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(invalid_xml)
        
        result = file_service.extract_test_case_description(xml_file)
        
        # 应该返回默认模板
        assert '【预置条件】' in result
        assert 'CBS系统运行正常' in result
        assert '【测试步骤】' in result
        assert '进行调账，调减20元' in result
        assert '【预期结果】' in result
        assert '调账成功' in result
    
    def test_extract_test_case_description_nonexistent_file(self, file_service):
        """测试不存在的文件时返回默认模板"""
        result = file_service.extract_test_case_description('/nonexistent/file.xml')
        
        # 应该返回默认模板
        assert '【预置条件】' in result
        assert 'CBS系统运行正常' in result
        assert '【测试步骤】' in result
        assert '进行调账，调减20元' in result
        assert '【预期结果】' in result
        assert '调账成功' in result
    
    def test_get_default_template(self, file_service):
        """测试获取默认模板"""
        result = file_service._get_default_template()
        
        assert '【预置条件】' in result
        assert '1. CBS系统运行正常' in result
        assert '2. 修改系统变量SYS_abc的值为12' in result
        assert '3. 设置变量，初始金额为100' in result
        assert '【测试步骤】' in result
        assert '1. 进行调账，调减20元' in result
        assert '【预期结果】' in result
        assert '1. 调账成功' in result
        assert '2. account_balance表amount字段值为80' in result


class TestFileServiceIntegration:
    """FileService集成测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_service(self, temp_dir):
        """创建FileService实例"""
        return FileService(temp_dir)
    
    def test_complete_workflow(self, file_service):
        """测试完整的文件处理工作流"""
        session_id = 'integration_test_session'
        
        # 1. 创建并保存XML文件
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testcases>
    <testcase id="TC001" name="集成测试">
        <steps>
            <step name="测试步骤">
                <component type="api" name="API调用">
                    <params>
                        <param name="method">POST</param>
                        <param name="url">/api/test</param>
                    </params>
                </component>
            </step>
        </steps>
    </testcase>
</testcases>'''
        
        # 模拟文件上传
        mock_file = Mock(spec=FileStorage)
        mock_file.filename = 'integration_test.xml'
        mock_file.save = Mock()
        
        def save_side_effect(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        mock_file.save.side_effect = save_side_effect
        
        # 2. 保存上传文件
        file_info = file_service.save_uploaded_file(mock_file, session_id, 'template')
        assert file_info['file_type'] == 'template'
        assert os.path.exists(file_info['file_path'])
        
        # 3. 解析XML文件
        parse_result = file_service.parse_xml_file(file_info['file_path'])
        assert parse_result['test_case_count'] == 1
        assert parse_result['test_cases'][0]['id'] == 'TC001'
        
        # 4. 生成新的测试用例
        new_test_cases = [
            {
                'id': 'TC002',
                'name': '生成的测试用例',
                'steps': [
                    {
                        'name': '新步骤',
                        'components': [
                            {
                                'type': 'assert',
                                'name': '验证结果',
                                'params': {
                                    'type': 'equals',
                                    'expected': 'success'
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        # 5. 生成XML输出
        generated_xml = file_service.generate_xml_output(new_test_cases)
        assert '<testcase id="TC002"' in generated_xml
        
        # 6. 保存生成的文件
        generated_file_info = file_service.save_generated_file(session_id, generated_xml)
        assert os.path.exists(generated_file_info['file_path'])
        
        # 7. 获取文件内容
        file_content = file_service.get_file_content(generated_file_info['file_path'])
        # 规范化行结束符进行比较
        expected_content = generated_xml.replace('\r\n', '\n').replace('\r', '\n')
        actual_content = file_content.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
        assert expected_content == actual_content
        
        # 8. 获取文件信息
        file_info_result = file_service.get_file_info(session_id, generated_file_info['file_id'])
        assert file_info_result is not None
        assert file_info_result['file_id'] == generated_file_info['file_id']
        
        # 9. 清理会话文件
        cleanup_result = file_service.cleanup_session_files(session_id)
        assert cleanup_result is True
        assert not os.path.exists(file_info['file_path'])
        assert not os.path.exists(generated_file_info['file_path'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])