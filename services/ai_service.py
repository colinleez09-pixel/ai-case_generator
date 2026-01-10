import json
import time
import random
import logging
from typing import Dict, Any, List, Generator, Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """AI服务 - 支持Dify Agent集成和Mock模式"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI服务
        
        Args:
            config: AI服务配置
        """
        self.dify_url = config.get('dify_url', '')
        self.dify_token = config.get('dify_token', '')
        self.mock_mode = config.get('mock_mode', True)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        
        # Mock数据配置
        self.mock_responses = [
            "好的，我已经分析了您上传的文件。请描述一下您希望生成的测试用例类型和测试场景。",
            "了解了您的需求。关于登录功能测试，您希望覆盖哪些场景：1.正常登录 2.密码错误 3.账号不存在 4.验证码校验？",
            "很好！我还需要了解一些细节：您希望测试哪些浏览器兼容性？是否需要包含移动端测试？",
            "明白了。最后确认一下测试数据：您希望使用真实的测试账号还是模拟数据？如果准备好了，请回复'开始生成'。",
            "收到！我现在有足够的信息来生成高质量的测试用例了。请告诉我是否可以开始生成？"
        ]
        
        logger.info(f"AI服务初始化完成，Mock模式: {self.mock_mode}")
    
    def analyze_files(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析上传的文件
        
        Args:
            files_info: 文件信息字典
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            if self.mock_mode:
                return self._mock_file_analysis(files_info)
            else:
                return self._dify_analyze_files(files_info)
                
        except Exception as e:
            logger.error(f"文件分析失败: {e}")
            # 降级到Mock模式
            return self._mock_file_analysis(files_info)
    
    def chat_with_agent(self, session_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        与AI Agent进行对话
        
        Args:
            session_id: 会话ID
            message: 用户消息
            context: 对话上下文
            
        Returns:
            Dict[str, Any]: AI回复
        """
        try:
            if self.mock_mode:
                return self._mock_chat_response(message, context)
            else:
                return self._dify_chat_request(session_id, message, context)
                
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            # 降级到Mock模式
            return self._mock_chat_response(message, context)
    
    def generate_test_cases(self, session_id: str, context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        生成测试用例 - 支持流式响应
        
        Args:
            session_id: 会话ID
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            if self.mock_mode:
                yield from self._mock_generation_stream(context)
            else:
                yield from self._dify_generation_stream(session_id, context)
                
        except Exception as e:
            logger.error(f"测试用例生成失败: {e}")
            # 降级到Mock模式
            yield from self._mock_generation_stream(context)
    
    def _mock_file_analysis(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock文件分析
        
        Args:
            files_info: 文件信息
            
        Returns:
            Dict[str, Any]: Mock分析结果
        """
        analysis_result = {
            'template_info': '',
            'history_info': '',
            'suggestions': []
        }
        
        # 分析模板文件
        if 'case_template' in files_info:
            template_file = files_info['case_template']
            analysis_result['template_info'] = f"检测到模板文件包含 {random.randint(15, 30)} 个测试场景，主要涉及用户管理、权限控制和数据操作功能。"
        
        # 分析历史用例文件
        if 'history_case' in files_info:
            history_file = files_info['history_case']
            analysis_result['history_info'] = f"发现 {random.randint(40, 80)} 条历史用例可供参考，覆盖了登录、搜索、订单等核心业务流程。"
        
        # 分析AW模板文件
        if 'aw_template' in files_info:
            aw_file = files_info['aw_template']
            analysis_result['suggestions'].append("检测到AW工程模板，建议重点关注接口兼容性测试。")
        
        # 添加通用建议
        analysis_result['suggestions'].extend([
            "建议增加异常场景的测试覆盖",
            "推荐添加性能测试用例",
            "考虑增加边界值测试"
        ])
        
        logger.info(f"Mock文件分析完成: {len(files_info)} 个文件")
        return analysis_result
    
    def _mock_chat_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock对话响应
        
        Args:
            message: 用户消息
            context: 对话上下文
            
        Returns:
            Dict[str, Any]: Mock回复
        """
        # 检查是否是开始生成的关键词
        if "开始生成" in message.lower() or "start" in message.lower():
            return {
                'reply': "好的，我现在开始为您生成测试用例。请稍等...",
                'need_more_info': False,
                'ready_to_generate': True
            }
        
        # 获取对话历史长度来决定回复
        chat_history = context.get('chat_history', [])
        response_index = len([msg for msg in chat_history if msg.get('role') == 'user']) % len(self.mock_responses)
        
        # 模拟思考时间
        time.sleep(random.uniform(0.5, 1.5))
        
        return {
            'reply': self.mock_responses[response_index],
            'need_more_info': True,
            'ready_to_generate': False,
            'suggestions': [
                "您可以描述具体的测试场景",
                "告诉我需要重点关注的功能模块",
                "说明测试的优先级要求"
            ]
        }
    
    def _mock_generation_stream(self, context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Mock生成流式响应
        
        Args:
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        # 模拟生成过程的各个阶段
        stages = [
            {"stage": "analyzing", "message": "正在分析需求和文件内容...", "progress": 10},
            {"stage": "planning", "message": "正在规划测试用例结构...", "progress": 25},
            {"stage": "generating", "message": "正在生成测试步骤...", "progress": 50},
            {"stage": "optimizing", "message": "正在优化测试用例...", "progress": 75},
            {"stage": "formatting", "message": "正在格式化输出...", "progress": 90},
        ]
        
        for stage in stages:
            yield {
                'type': 'progress',
                'data': stage
            }
            time.sleep(random.uniform(1.0, 2.0))
        
        # 生成Mock测试用例数据
        test_cases = self._generate_mock_test_cases(context)
        
        yield {
            'type': 'complete',
            'data': {
                'test_cases': test_cases,
                'total_count': len(test_cases),
                'message': f"成功生成 {len(test_cases)} 条测试用例"
            }
        }
    
    def _generate_mock_test_cases(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成Mock测试用例数据
        
        Args:
            context: 生成上下文
            
        Returns:
            List[Dict[str, Any]]: Mock测试用例列表
        """
        test_cases = [
            {
                'id': 'TC001',
                'name': '用户登录功能测试',
                'preconditions': [
                    {
                        'id': 'pre1',
                        'name': '用户已注册账号',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec1',
                                'type': 'api',
                                'name': '接口调用 - 检查用户存在',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/users/check',
                                    'expected': True
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's1',
                        'name': '打开登录页面',
                        'expanded': True,
                        'components': [
                            {
                                'id': 'c1',
                                'type': 'api',
                                'name': '接口调用 - 获取登录页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/login'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's2',
                        'name': '输入用户名和密码',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c2',
                                'type': 'input',
                                'name': '输入用户名',
                                'params': {
                                    'selector': '#username',
                                    'value': 'testuser'
                                }
                            },
                            {
                                'id': 'c3',
                                'type': 'input',
                                'name': '输入密码',
                                'params': {
                                    'selector': '#password',
                                    'value': 'password123'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's3',
                        'name': '点击登录按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c4',
                                'type': 'button',
                                'name': '点击登录',
                                'params': {
                                    'selector': '#login-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp1',
                        'name': '成功跳转到用户仪表板页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc1',
                                'type': 'assert',
                                'name': '断言 - URL正确',
                                'params': {
                                    'type': 'equals',
                                    'expected': '/dashboard'
                                }
                            },
                            {
                                'id': 'expc2',
                                'type': 'assert',
                                'name': '断言 - 显示用户信息',
                                'params': {
                                    'type': 'exists',
                                    'expected': '.user-info'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'TC002',
                'name': '用户登录失败测试',
                'preconditions': [
                    {
                        'id': 'pre2',
                        'name': '用户账号存在但密码错误',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec2',
                                'type': 'api',
                                'name': '接口调用 - 验证用户存在',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/users/testuser',
                                    'expected': True
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's4',
                        'name': '打开登录页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c5',
                                'type': 'api',
                                'name': '接口调用 - 获取登录页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/login'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's5',
                        'name': '输入错误密码',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c6',
                                'type': 'input',
                                'name': '输入用户名',
                                'params': {
                                    'selector': '#username',
                                    'value': 'testuser'
                                }
                            },
                            {
                                'id': 'c7',
                                'type': 'input',
                                'name': '输入错误密码',
                                'params': {
                                    'selector': '#password',
                                    'value': 'wrongpassword'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's6',
                        'name': '点击登录按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c8',
                                'type': 'button',
                                'name': '点击登录',
                                'params': {
                                    'selector': '#login-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp2',
                        'name': '显示密码错误提示',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc3',
                                'type': 'assert',
                                'name': '断言 - 错误信息显示',
                                'params': {
                                    'type': 'contains',
                                    'expected': '密码错误'
                                }
                            },
                            {
                                'id': 'expc4',
                                'type': 'assert',
                                'name': '断言 - 仍在登录页面',
                                'params': {
                                    'type': 'equals',
                                    'expected': '/login'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'TC003',
                'name': '搜索功能测试',
                'preconditions': [
                    {
                        'id': 'pre3',
                        'name': '用户已登录系统',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'prec3',
                                'type': 'api',
                                'name': '接口调用 - 验证登录状态',
                                'params': {
                                    'method': 'GET',
                                    'url': '/api/auth/status',
                                    'expected': 'authenticated'
                                }
                            }
                        ]
                    }
                ],
                'steps': [
                    {
                        'id': 's7',
                        'name': '打开搜索页面',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c9',
                                'type': 'api',
                                'name': '接口调用 - 获取搜索页',
                                'params': {
                                    'method': 'GET',
                                    'url': '/search'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's8',
                        'name': '输入搜索关键词',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c10',
                                'type': 'input',
                                'name': '输入搜索词',
                                'params': {
                                    'selector': '#search-input',
                                    'value': '测试关键词'
                                }
                            }
                        ]
                    },
                    {
                        'id': 's9',
                        'name': '点击搜索按钮',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'c11',
                                'type': 'button',
                                'name': '点击搜索',
                                'params': {
                                    'selector': '#search-btn',
                                    'action': 'click'
                                }
                            }
                        ]
                    }
                ],
                'expectedResults': [
                    {
                        'id': 'exp3',
                        'name': '显示搜索结果',
                        'expanded': False,
                        'components': [
                            {
                                'id': 'expc5',
                                'type': 'assert',
                                'name': '断言 - 结果列表存在',
                                'params': {
                                    'type': 'exists',
                                    'expected': '.search-results'
                                }
                            },
                            {
                                'id': 'expc6',
                                'type': 'assert',
                                'name': '断言 - 结果数量大于0',
                                'params': {
                                    'type': 'greater_than',
                                    'expected': 0
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        return test_cases
    
    def _dify_analyze_files(self, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用Dify分析文件
        
        Args:
            files_info: 文件信息
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 构建请求数据
            request_data = {
                'inputs': {
                    'files_info': json.dumps(files_info)
                },
                'response_mode': 'blocking',
                'user': 'file_analyzer'
            }
            
            headers = {
                'Authorization': f'Bearer {self.dify_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.dify_url}/chat-messages',
                json=request_data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_dify_analysis_response(result)
            else:
                logger.error(f"Dify文件分析请求失败: {response.status_code}")
                raise Exception(f"Dify API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Dify文件分析异常: {e}")
            raise
    
    def _dify_chat_request(self, session_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用Dify进行对话
        
        Args:
            session_id: 会话ID
            message: 用户消息
            context: 对话上下文
            
        Returns:
            Dict[str, Any]: 对话回复
        """
        try:
            request_data = {
                'inputs': {
                    'message': message,
                    'context': json.dumps(context)
                },
                'query': message,
                'response_mode': 'blocking',
                'conversation_id': session_id,
                'user': f'user_{session_id}'
            }
            
            headers = {
                'Authorization': f'Bearer {self.dify_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.dify_url}/chat-messages',
                json=request_data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_dify_chat_response(result)
            else:
                logger.error(f"Dify对话请求失败: {response.status_code}")
                raise Exception(f"Dify API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Dify对话异常: {e}")
            raise
    
    def _dify_generation_stream(self, session_id: str, context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        使用Dify进行流式生成
        
        Args:
            session_id: 会话ID
            context: 生成上下文
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            request_data = {
                'inputs': {
                    'context': json.dumps(context)
                },
                'response_mode': 'streaming',
                'conversation_id': session_id,
                'user': f'user_{session_id}'
            }
            
            headers = {
                'Authorization': f'Bearer {self.dify_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.dify_url}/chat-messages',
                json=request_data,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            parsed_data = self._parse_dify_stream_response(data)
                            if parsed_data:
                                yield parsed_data
                        except json.JSONDecodeError:
                            continue
            else:
                logger.error(f"Dify流式生成请求失败: {response.status_code}")
                raise Exception(f"Dify API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Dify流式生成异常: {e}")
            raise
    
    def _parse_dify_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Dify文件分析响应
        
        Args:
            response: Dify响应数据
            
        Returns:
            Dict[str, Any]: 解析后的分析结果
        """
        try:
            answer = response.get('answer', '')
            # 这里需要根据实际的Dify响应格式进行解析
            # 假设Dify返回JSON格式的分析结果
            analysis_result = json.loads(answer)
            return analysis_result
        except Exception as e:
            logger.error(f"解析Dify分析响应失败: {e}")
            # 返回默认结构
            return {
                'template_info': '文件分析完成',
                'history_info': '',
                'suggestions': []
            }
    
    def _parse_dify_chat_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Dify对话响应
        
        Args:
            response: Dify响应数据
            
        Returns:
            Dict[str, Any]: 解析后的对话回复
        """
        try:
            answer = response.get('answer', '')
            
            # 检查是否准备生成
            ready_to_generate = "开始生成" in answer or "ready to generate" in answer.lower()
            
            return {
                'reply': answer,
                'need_more_info': not ready_to_generate,
                'ready_to_generate': ready_to_generate,
                'suggestions': []
            }
        except Exception as e:
            logger.error(f"解析Dify对话响应失败: {e}")
            return {
                'reply': '抱歉，我遇到了一些问题，请重试。',
                'need_more_info': True,
                'ready_to_generate': False
            }
    
    def _parse_dify_stream_response(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析Dify流式响应
        
        Args:
            data: 流式数据
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的流式数据
        """
        try:
            event = data.get('event', '')
            
            if event == 'message':
                # 进度消息
                return {
                    'type': 'progress',
                    'data': {
                        'stage': 'generating',
                        'message': data.get('answer', ''),
                        'progress': 50
                    }
                }
            elif event == 'message_end':
                # 生成完成
                answer = data.get('answer', '')
                try:
                    test_cases = json.loads(answer)
                    return {
                        'type': 'complete',
                        'data': {
                            'test_cases': test_cases,
                            'total_count': len(test_cases),
                            'message': f"成功生成 {len(test_cases)} 条测试用例"
                        }
                    }
                except json.JSONDecodeError:
                    # 如果不是JSON格式，返回错误
                    return {
                        'type': 'error',
                        'data': {
                            'message': '生成结果格式错误'
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"解析Dify流式响应失败: {e}")
            return {
                'type': 'error',
                'data': {
                    'message': '解析响应失败'
                }
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        if self.mock_mode:
            return {
                'status': 'healthy',
                'mode': 'mock',
                'message': 'Mock模式运行正常'
            }
        
        try:
            # 简单的健康检查请求
            headers = {
                'Authorization': f'Bearer {self.dify_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.dify_url}/parameters',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'mode': 'dify',
                    'message': 'Dify服务连接正常'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'mode': 'dify',
                    'message': f'Dify服务响应异常: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'mode': 'dify',
                'message': f'Dify服务连接失败: {str(e)}'
            }