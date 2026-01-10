import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class FileService:
    """文件处理服务"""
    
    def __init__(self, upload_folder: str):
        """
        初始化文件服务
        
        Args:
            upload_folder: 文件上传目录
        """
        self.upload_folder = upload_folder
        self.allowed_extensions = {'xml'}
        
        # 确保上传目录存在
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
    
    def is_allowed_file(self, filename: str) -> bool:
        """
        检查文件扩展名是否允许
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否允许的文件类型
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_uploaded_file(self, file: FileStorage, session_id: str, file_type: str) -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            session_id: 会话ID
            file_type: 文件类型 (history|template|aw)
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        try:
            if not file or file.filename == '':
                raise ValueError("没有选择文件")
            
            if not self.is_allowed_file(file.filename):
                raise ValueError(f"不支持的文件类型，只支持: {', '.join(self.allowed_extensions)}")
            
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            file_id = f"{file_type}_{uuid.uuid4().hex[:8]}"
            filename = f"{session_id}_{file_id}_{original_filename}"
            
            # 创建会话专用目录
            session_dir = os.path.join(self.upload_folder, session_id)
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
            
            # 保存文件
            file_path = os.path.join(session_dir, filename)
            file.save(file_path)
            
            # 验证文件是否为有效的XML
            try:
                self.parse_xml_file(file_path)
            except Exception as e:
                # 删除无效文件
                os.remove(file_path)
                raise ValueError(f"XML文件格式错误: {str(e)}")
            
            file_info = {
                'file_id': file_id,
                'original_name': original_filename,
                'saved_name': filename,
                'file_path': file_path,
                'file_type': file_type,
                'file_size': os.path.getsize(file_path),
                'upload_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"文件保存成功: {filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise
    
    def parse_xml_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析XML文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 基本信息
            result = {
                'root_tag': root.tag,
                'total_elements': len(list(root.iter())),
                'attributes': dict(root.attrib) if root.attrib else {},
                'structure': self._analyze_xml_structure(root)
            }
            
            # 如果是测试用例文件，进行特殊解析
            if root.tag.lower() in ['testcases', 'testcase', 'testsuite']:
                result.update(self._parse_test_case_xml(root))
            
            logger.debug(f"XML文件解析成功: {file_path}")
            return result
            
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {file_path}, {e}")
            raise ValueError(f"XML格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"文件解析失败: {file_path}, {e}")
            raise
    
    def _analyze_xml_structure(self, element: ET.Element, max_depth: int = 3) -> Dict[str, Any]:
        """
        分析XML结构
        
        Args:
            element: XML元素
            max_depth: 最大分析深度
            
        Returns:
            Dict[str, Any]: 结构信息
        """
        if max_depth <= 0:
            return {'tag': element.tag, 'children_count': len(element)}
        
        structure = {
            'tag': element.tag,
            'text': element.text.strip() if element.text else None,
            'attributes': dict(element.attrib) if element.attrib else {},
            'children': []
        }
        
        # 分析子元素
        child_tags = {}
        for child in element:
            if child.tag not in child_tags:
                child_tags[child.tag] = 0
            child_tags[child.tag] += 1
        
        # 只保留结构信息，不递归太深
        for tag, count in child_tags.items():
            structure['children'].append({
                'tag': tag,
                'count': count
            })
        
        return structure
    
    def _parse_test_case_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        解析测试用例XML的特殊信息
        
        Args:
            root: XML根元素
            
        Returns:
            Dict[str, Any]: 测试用例信息
        """
        result = {
            'test_case_count': 0,
            'test_cases': [],
            'categories': set(),
            'priorities': set()
        }
        
        # 查找测试用例元素
        test_case_elements = []
        if root.tag.lower() == 'testcase':
            test_case_elements = [root]
        else:
            test_case_elements = root.findall('.//testcase') or root.findall('.//TestCase')
        
        result['test_case_count'] = len(test_case_elements)
        
        # 分析前几个测试用例的结构
        for i, tc in enumerate(test_case_elements[:5]):  # 只分析前5个
            case_info = {
                'id': tc.get('id') or tc.get('ID') or f'case_{i+1}',
                'name': tc.get('name') or tc.get('title') or tc.text or 'Unknown',
                'attributes': dict(tc.attrib)
            }
            
            # 收集分类和优先级信息
            if 'category' in tc.attrib:
                result['categories'].add(tc.attrib['category'])
            if 'priority' in tc.attrib:
                result['priorities'].add(tc.attrib['priority'])
            
            result['test_cases'].append(case_info)
        
        # 转换set为list以便JSON序列化
        result['categories'] = list(result['categories'])
        result['priorities'] = list(result['priorities'])
        
        return result
    
    def generate_xml_output(self, test_cases: List[Dict[str, Any]]) -> str:
        """
        生成XML格式的测试用例文件
        
        Args:
            test_cases: 测试用例数据列表
            
        Returns:
            str: XML内容
        """
        try:
            # 创建根元素
            root = ET.Element('testcases')
            root.set('generated_at', datetime.utcnow().isoformat())
            root.set('count', str(len(test_cases)))
            
            for tc in test_cases:
                # 创建测试用例元素
                testcase = ET.SubElement(root, 'testcase')
                testcase.set('id', tc.get('id', ''))
                testcase.set('name', tc.get('name', ''))
                
                # 添加预置条件
                if tc.get('preconditions'):
                    preconditions = ET.SubElement(testcase, 'preconditions')
                    for i, pre in enumerate(tc['preconditions']):
                        precondition = ET.SubElement(preconditions, 'precondition')
                        precondition.set('index', str(i + 1))
                        precondition.set('name', pre.get('name', ''))
                        
                        # 添加组件
                        if pre.get('components'):
                            for comp in pre['components']:
                                component = ET.SubElement(precondition, 'component')
                                component.set('type', comp.get('type', ''))
                                component.set('name', comp.get('name', ''))
                                
                                # 添加参数
                                if comp.get('params'):
                                    params = ET.SubElement(component, 'params')
                                    for key, value in comp['params'].items():
                                        param = ET.SubElement(params, 'param')
                                        param.set('name', key)
                                        param.text = str(value)
                
                # 添加测试步骤
                if tc.get('steps'):
                    steps = ET.SubElement(testcase, 'steps')
                    for i, step in enumerate(tc['steps']):
                        step_elem = ET.SubElement(steps, 'step')
                        step_elem.set('index', str(i + 1))
                        step_elem.set('name', step.get('name', ''))
                        
                        # 添加组件
                        if step.get('components'):
                            for comp in step['components']:
                                component = ET.SubElement(step_elem, 'component')
                                component.set('type', comp.get('type', ''))
                                component.set('name', comp.get('name', ''))
                                
                                # 添加参数
                                if comp.get('params'):
                                    params = ET.SubElement(component, 'params')
                                    for key, value in comp['params'].items():
                                        param = ET.SubElement(params, 'param')
                                        param.set('name', key)
                                        param.text = str(value)
                
                # 添加预期结果
                if tc.get('expectedResults'):
                    expected_results = ET.SubElement(testcase, 'expectedResults')
                    for i, result in enumerate(tc['expectedResults']):
                        result_elem = ET.SubElement(expected_results, 'expectedResult')
                        result_elem.set('index', str(i + 1))
                        result_elem.set('name', result.get('name', ''))
                        
                        # 添加组件
                        if result.get('components'):
                            for comp in result['components']:
                                component = ET.SubElement(result_elem, 'component')
                                component.set('type', comp.get('type', ''))
                                component.set('name', comp.get('name', ''))
                                
                                # 添加参数
                                if comp.get('params'):
                                    params = ET.SubElement(component, 'params')
                                    for key, value in comp['params'].items():
                                        param = ET.SubElement(params, 'param')
                                        param.set('name', key)
                                        param.text = str(value)
            
            # 格式化XML
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            formatted_xml = reparsed.toprettyxml(indent="  ", encoding=None)
            
            # 移除空行
            lines = [line for line in formatted_xml.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"生成XML失败: {e}")
            raise ValueError(f"XML生成失败: {str(e)}")
    
    def save_generated_file(self, session_id: str, xml_content: str) -> Dict[str, Any]:
        """
        保存生成的XML文件
        
        Args:
            session_id: 会话ID
            xml_content: XML内容
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        try:
            file_id = f"generated_{uuid.uuid4().hex[:8]}"
            filename = f"{session_id}_{file_id}_test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            # 创建会话目录
            session_dir = os.path.join(self.upload_folder, session_id)
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
            
            file_path = os.path.join(session_dir, filename)
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            file_info = {
                'file_id': file_id,
                'filename': filename,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"生成文件保存成功: {filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"保存生成文件失败: {e}")
            raise
    
    def get_file_content(self, file_path: str) -> bytes:
        """
        获取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            bytes: 文件内容
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            raise
    
    def cleanup_session_files(self, session_id: str) -> bool:
        """
        清理会话相关的临时文件
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 清理是否成功
        """
        try:
            session_dir = os.path.join(self.upload_folder, session_id)
            
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                logger.info(f"清理会话文件成功: {session_id}")
                return True
            else:
                logger.warning(f"会话目录不存在: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"清理会话文件失败: {session_id}, {e}")
            return False
    
    def get_file_info(self, session_id: str, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
            
        Returns:
            Dict[str, Any]: 文件信息，如果文件不存在返回None
        """
        try:
            session_dir = os.path.join(self.upload_folder, session_id)
            
            if not os.path.exists(session_dir):
                return None
            
            # 查找匹配的文件
            for filename in os.listdir(session_dir):
                if file_id in filename:
                    file_path = os.path.join(session_dir, filename)
                    return {
                        'file_id': file_id,
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': os.path.getsize(file_path),
                        'modified_time': datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {session_id}/{file_id}, {e}")
            return None