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
import hashlib
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

class FileService:
    """文件处理服务 - 增强版本支持性能优化和缓存"""
    
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
        
        # 性能优化配置
        self.performance_config = {
            'enable_xml_cache': True,
            'cache_ttl': 300,  # 缓存5分钟
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'fast_parse_threshold': 1024 * 1024,  # 1MB以下使用快速解析
            'enable_parallel_processing': True
        }
        
        # XML解析缓存
        self._xml_cache = {}
        self._cache_timestamps = {}
        
        logger.info(f"FileService初始化完成，上传目录: {upload_folder}")
        logger.info(f"性能优化配置: {self.performance_config}")
    
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
    
    def _get_cached_parse_result(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的解析结果"""
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(file_path)
            
            # 检查缓存是否存在且未过期
            if cache_key in self._xml_cache:
                cache_time = self._cache_timestamps.get(cache_key, 0)
                if time.time() - cache_time < self.performance_config['cache_ttl']:
                    # 验证文件是否被修改
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime <= cache_time:
                        return self._xml_cache[cache_key]
                
                # 缓存过期或文件已修改，清除缓存
                self._remove_cache_entry(cache_key)
            
            return None
            
        except Exception as e:
            logger.warning(f"获取缓存失败: {e}")
            return None
    
    def _cache_parse_result(self, file_path: str, result: Dict[str, Any]):
        """缓存解析结果"""
        try:
            cache_key = self._generate_cache_key(file_path)
            self._xml_cache[cache_key] = result.copy()
            self._cache_timestamps[cache_key] = time.time()
            
            # 清理过期缓存
            self._cleanup_expired_cache()
            
        except Exception as e:
            logger.warning(f"缓存解析结果失败: {e}")
    
    def _generate_cache_key(self, file_path: str) -> str:
        """生成缓存键"""
        # 使用文件路径和修改时间生成唯一键
        file_stat = os.stat(file_path)
        key_data = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _remove_cache_entry(self, cache_key: str):
        """移除缓存条目"""
        self._xml_cache.pop(cache_key, None)
        self._cache_timestamps.pop(cache_key, None)
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_time in self._cache_timestamps.items():
            if current_time - cache_time >= self.performance_config['cache_ttl']:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        if expired_keys:
            logger.debug(f"清理过期缓存: {len(expired_keys)} 个条目")

    def parse_xml_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析XML文件内容 - 性能优化版本
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        start_time = time.time()
        
        # 检查缓存
        if self.performance_config['enable_xml_cache']:
            cache_result = self._get_cached_parse_result(file_path)
            if cache_result is not None:
                parse_time = time.time() - start_time
                logger.debug(f"XML解析缓存命中: {file_path}, 耗时: {parse_time:.3f}s")
                return cache_result
        
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            logger.debug(f"开始解析XML文件: {file_path}, 大小: {file_size} 字节")
            
            if file_size > self.performance_config['max_file_size']:
                raise ValueError(f"文件过大: {file_size} 字节，超过限制 {self.performance_config['max_file_size']} 字节")
            
            # 解析XML
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
            
            parse_time = time.time() - start_time
            logger.debug(f"XML解析完成: {file_path}, 耗时: {parse_time:.3f}s")
            
            # 缓存结果
            if self.performance_config['enable_xml_cache']:
                self._cache_parse_result(file_path, result)
            
            return result
            
        except ET.ParseError as e:
            # 详细记录XML解析错误
            logger.error(f"XML解析错误详情:")
            logger.error(f"  文件路径: {file_path}")
            logger.error(f"  错误类型: XML格式错误")
            logger.error(f"  错误信息: {str(e)}")
            logger.error(f"  错误位置: 行 {getattr(e, 'lineno', '未知')}, 列 {getattr(e, 'offset', '未知')}")
            
            # 尝试读取文件内容的前几行用于调试
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]  # 只读取前5行
                    logger.error(f"  文件前5行内容:")
                    for i, line in enumerate(lines, 1):
                        logger.error(f"    {i}: {line.strip()}")
            except Exception as read_error:
                logger.error(f"  无法读取文件内容: {read_error}")
            
            raise ValueError(f"XML格式错误: {str(e)}")
        except Exception as e:
            # 详细记录其他解析错误
            logger.error(f"XML文件解析失败详情:")
            logger.error(f"  文件路径: {file_path}")
            logger.error(f"  错误类型: {type(e).__name__}")
            logger.error(f"  错误信息: {str(e)}")
            logger.error(f"  文件大小: {os.path.getsize(file_path) if os.path.exists(file_path) else '文件不存在'} 字节")
            
            # 记录文件编码信息
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read(1024)  # 读取前1KB用于编码检测
                    encoding_info = chardet.detect(raw_data)
                    logger.error(f"  检测到的文件编码: {encoding_info}")
            except Exception as encoding_error:
                logger.error(f"  编码检测失败: {encoding_error}")
            
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
    
    def extract_test_case_description(self, file_path: str) -> str:
        """
        从XML文件中提取测试用例描述 - 只提取第一个测试用例
        
        Args:
            file_path: XML文件路径
            
        Returns:
            str: 格式化的测试用例描述（仅第一个测试用例）
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 查找第一个测试用例
            first_testcase = None
            
            # 尝试多种可能的测试用例标签名称
            testcase_candidates = (
                root.findall('.//testcase') or 
                root.findall('.//TestCase') or
                root.findall('.//测试用例') or
                root.findall('.//test_case') or
                root.findall('.//case')
            )
            
            if testcase_candidates:
                # 取第一个测试用例
                first_testcase = testcase_candidates[0]
                logger.info(f"找到 {len(testcase_candidates)} 个测试用例，只提取第一个")
            elif root.tag.lower() in ['testcase', 'testcases', '测试用例', '测试用例集']:
                # 如果根元素就是测试用例容器，查找其中的第一个子测试用例
                for child in root:
                    if child.tag.lower() in ['testcase', '测试用例', 'test_case', 'case']:
                        first_testcase = child
                        logger.info(f"从根元素中找到第一个测试用例: {child.tag}")
                        break
                
                # 如果没有找到子测试用例，将根元素作为测试用例
                if first_testcase is None:
                    first_testcase = root
                    logger.info("将根元素作为测试用例处理")
            else:
                # 如果根元素本身就是一个测试用例
                first_testcase = root
                logger.info("将根元素作为单个测试用例处理")
            
            if first_testcase is None:
                logger.warning(f"未找到测试用例结构，使用默认模板: {file_path}")
                return self._get_default_template()
            
            # 从第一个测试用例中提取信息
            preconditions = []
            steps = []
            expected_results = []
            
            # 提取预置条件
            for pre in (first_testcase.findall('.//precondition') or 
                       first_testcase.findall('.//前置条件') or 
                       first_testcase.findall('.//condition') or
                       first_testcase.findall('.//条件')):
                if pre.text and pre.text.strip():
                    preconditions.append(pre.text.strip())
                # 如果元素有子元素，尝试提取子元素的文本
                elif len(pre) > 0:
                    for child in pre:
                        if child.text and child.text.strip():
                            preconditions.append(child.text.strip())
            
            # 提取测试步骤
            for step in (first_testcase.findall('.//step') or 
                        first_testcase.findall('.//测试步骤') or 
                        first_testcase.findall('.//步骤')):
                if step.text and step.text.strip():
                    steps.append(step.text.strip())
                # 如果元素有子元素，尝试提取子元素的文本
                elif len(step) > 0:
                    for child in step:
                        if child.text and child.text.strip():
                            steps.append(child.text.strip())
            
            # 提取预期结果
            for result in (first_testcase.findall('.//expected') or 
                          first_testcase.findall('.//预期结果') or 
                          first_testcase.findall('.//result') or
                          first_testcase.findall('.//结果')):
                if result.text and result.text.strip():
                    expected_results.append(result.text.strip())
                # 如果元素有子元素，尝试提取子元素的文本
                elif len(result) > 0:
                    for child in result:
                        if child.text and child.text.strip():
                            expected_results.append(child.text.strip())
            
            # 如果没有找到结构化数据，尝试从测试用例的直接子元素中提取
            if not preconditions and not steps and not expected_results:
                for child in first_testcase:
                    if child.tag.lower() in ['precondition', '前置条件', 'setup']:
                        if child.text and child.text.strip():
                            preconditions.append(child.text.strip())
                        # 处理嵌套的条件
                        elif len(child) > 0:
                            for grandchild in child:
                                if grandchild.text and grandchild.text.strip():
                                    preconditions.append(grandchild.text.strip())
                    elif child.tag.lower() in ['step', 'action', '步骤', '测试步骤']:
                        if child.text and child.text.strip():
                            steps.append(child.text.strip())
                        # 处理嵌套的步骤
                        elif len(child) > 0:
                            for grandchild in child:
                                if grandchild.text and grandchild.text.strip():
                                    steps.append(grandchild.text.strip())
                    elif child.tag.lower() in ['expected', 'result', '预期结果', 'verification']:
                        if child.text and child.text.strip():
                            expected_results.append(child.text.strip())
                        # 处理嵌套的结果
                        elif len(child) > 0:
                            for grandchild in child:
                                if grandchild.text and grandchild.text.strip():
                                    expected_results.append(grandchild.text.strip())
            
            # 格式化输出
            description_parts = []
            
            # 添加测试用例名称（如果有）
            testcase_name = first_testcase.get('名称') or first_testcase.get('name') or first_testcase.get('title')
            if testcase_name:
                description_parts.append(f"【测试用例】{testcase_name}")
                description_parts.append("")
            
            if preconditions:
                description_parts.append("【预置条件】")
                for i, condition in enumerate(preconditions, 1):
                    description_parts.append(f"{i}. {condition}")
                description_parts.append("")
            
            if steps:
                description_parts.append("【测试步骤】")
                for i, step in enumerate(steps, 1):
                    description_parts.append(f"{i}. {step}")
                description_parts.append("")
            
            if expected_results:
                description_parts.append("【预期结果】")
                for i, result in enumerate(expected_results, 1):
                    description_parts.append(f"{i}. {result}")
            
            # 如果提取到了内容，返回格式化的描述
            if description_parts:
                extracted_content = "\n".join(description_parts)
                logger.info(f"成功提取第一个测试用例: {len(preconditions)} 个预置条件，{len(steps)} 个测试步骤，{len(expected_results)} 个预期结果")
                return extracted_content
            else:
                # 如果没有提取到结构化内容，返回默认模板
                logger.warning(f"第一个测试用例中未找到结构化内容，使用默认模板: {file_path}")
                return self._get_default_template()
            
        except ET.ParseError as e:
            # 详细记录XML解析失败
            logger.warning(f"XML解析失败详情:")
            logger.warning(f"  文件路径: {file_path}")
            logger.warning(f"  解析错误: {str(e)}")
            logger.warning(f"  错误位置: 行 {getattr(e, 'lineno', '未知')}")
            logger.warning(f"  将使用默认模板替代")
            return self._get_default_template()
        except Exception as e:
            # 详细记录其他处理错误
            logger.warning(f"XML文件处理失败详情:")
            logger.warning(f"  文件路径: {file_path}")
            logger.warning(f"  错误类型: {type(e).__name__}")
            logger.warning(f"  错误信息: {str(e)}")
            logger.warning(f"  将使用默认模板替代")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """获取默认测试用例模板"""
        return """【预置条件】
1. CBS系统运行正常
2. 修改系统变量SYS_abc的值为12
3. 设置变量，初始金额为100

【测试步骤】
1. 进行调账，调减20元

【预期结果】
1. 调账成功
2. account_balance表amount字段值为80"""

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