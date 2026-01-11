import logging
from typing import Dict, Any, List, Generator, Optional
from datetime import datetime
from services.file_service import FileService
from services.session_service import SessionService
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class GenerationService:
    """生成服务 - 协调测试用例生成的完整流程"""
    
    def __init__(self, file_service: FileService, session_service: SessionService, ai_service: AIService):
        """
        初始化生成服务
        
        Args:
            file_service: 文件服务实例
            session_service: 会话服务实例
            ai_service: AI服务实例
        """
        self.file_service = file_service
        self.session_service = session_service
        self.ai_service = ai_service
        
        logger.info("生成服务初始化完成")
    
    def start_generation_task(self, files: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动生成任务 - 同步包装方法
        
        Args:
            files: 上传的文件字典 {file_type: FileStorage}
            config: 配置信息
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        import asyncio
        
        # 如果当前没有事件循环，创建一个新的
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._start_generation_task_async(files, config))
                    return future.result()
            else:
                return loop.run_until_complete(self._start_generation_task_async(files, config))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self._start_generation_task_async(files, config))
    
    async def _start_generation_task_async(self, files: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动生成任务 - 异步实现
        
        Args:
            files: 上传的文件字典 {file_type: FileStorage}
            config: 配置信息
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        try:
            # 1. 创建新会话
            session_id = self.session_service.create_session()
            logger.info(f"创建生成会话: {session_id}")
            
            # 2. 保存上传的文件
            files_info = {}
            for file_type, file_storage in files.items():
                if file_storage and file_storage.filename:
                    try:
                        file_info = self.file_service.save_uploaded_file(
                            file_storage, session_id, file_type
                        )
                        files_info[file_type] = file_info
                        logger.info(f"保存文件成功: {file_type} -> {file_info['file_id']}")
                    except Exception as e:
                        logger.error(f"保存文件失败: {file_type}, {e}")
                        # 清理已创建的会话和文件
                        self._cleanup_failed_session(session_id)
                        return {
                            'success': False,
                            'error': 'file_save_failed',
                            'message': f'文件保存失败: {str(e)}'
                        }
            
            # 验证必需文件
            if 'case_template' not in files_info:
                self._cleanup_failed_session(session_id)
                return {
                    'success': False,
                    'error': 'missing_required_file',
                    'message': '缺少必需的用例模板文件'
                }
            
            # 3. 分析上传的文件（但不发送给Dify，避免重复调用）
            try:
                analysis_result = self.ai_service.analyze_files(files_info, skip_dify_call=True)
                logger.info(f"文件分析完成（跳过Dify调用）: {session_id}")
            except Exception as e:
                logger.error(f"文件分析失败: {session_id}, {e}")
                analysis_result = {
                    'template_info': '文件分析遇到问题，但可以继续',
                    'history_info': '',
                    'suggestions': ['请描述您的测试需求']
                }
            
            # 4. 更新会话数据
            session_data = {
                'status': 'analyzing',
                'files': files_info,
                'config': config,
                'analysis_result': analysis_result,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            update_result = self.session_service.update_session_data(session_id, session_data)
            if not update_result:
                self._cleanup_failed_session(session_id)
                return {
                    'success': False,
                    'error': 'session_update_failed',
                    'message': '更新会话数据失败'
                }
            
            # 5. 构建初始消息
            initial_message = self._build_initial_message(analysis_result)
            
            # 新增：自动解析并发送给AI (新增功能)
            logger.info(f"检查自动分析条件: analysis_result.success = {analysis_result.get('success', True)}")
            if analysis_result.get('success', True):
                try:
                    logger.info(f"开始自动分析流程: {session_id}")
                    # 先提取用例描述
                    extracted_content = self._extract_test_case_content(files_info)
                    logger.info(f"提取用例内容成功: {len(extracted_content)} 字符")
                    
                    # 将提取的内容添加到analysis_result中
                    analysis_result['description'] = extracted_content
                    analysis_result['extracted_content'] = extracted_content
                    
                    auto_analysis_result = await self.auto_analyze_and_chat(session_id, files_info)
                    logger.info(f"自动分析结果: success={auto_analysis_result.get('success')}")
                    
                    if auto_analysis_result.get('success'):
                        # 更新会话状态为chatting，准备接收用户输入
                        self.session_service.update_session_data(session_id, {
                            'status': 'chatting',
                            'initial_ai_response': auto_analysis_result.get('reply', ''),
                            'dify_conversation_id': auto_analysis_result.get('conversation_id'),
                            'extracted_content': extracted_content
                        })
                        logger.info(f"自动分析完成: {session_id}")
                        return {
                            'success': True,
                            'session_id': session_id,
                            'message': auto_analysis_result.get('reply', '文件分析完成'),
                            'initial_analysis': analysis_result,
                            'auto_chat_started': True,
                            'files_processed': len(files_info),
                            'extracted_content': extracted_content
                        }
                    else:
                        logger.warning(f"自动分析失败: {auto_analysis_result.get('error', 'unknown')}")
                except Exception as e:
                    logger.error(f"自动分析异常: {session_id}, {e}")
                    import traceback
                    logger.error(f"异常详情: {traceback.format_exc()}")
            else:
                logger.info(f"跳过自动分析: analysis_result.success = {analysis_result.get('success')}")
            
            # 原有返回逻辑保持不变
            return {
                'success': True,
                'session_id': session_id,
                'message': initial_message,
                'initial_analysis': analysis_result,
                'files_processed': len(files_info)
            }
            
        except Exception as e:
            logger.error(f"启动生成任务失败: {e}")
            return {
                'success': False,
                'error': 'generation_start_failed',
                'message': '启动生成任务失败，请重试'
            }
    
    def generate_test_cases_stream(self, session_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        流式生成测试用例
        
        Args:
            session_id: 会话ID
            
        Yields:
            Dict[str, Any]: 流式响应数据
        """
        try:
            # 1. 验证会话状态
            if not self.session_service.is_session_valid(session_id):
                yield {
                    'type': 'error',
                    'data': {
                        'error': 'session_invalid',
                        'message': '会话无效或已过期'
                    }
                }
                return
            
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                yield {
                    'type': 'error',
                    'data': {
                        'error': 'session_not_found',
                        'message': '会话数据不存在'
                    }
                }
                return
            
            # 验证会话状态
            if session_data.get('status') != 'ready_to_generate':
                yield {
                    'type': 'error',
                    'data': {
                        'error': 'invalid_status',
                        'message': f"会话状态不正确: {session_data.get('status')}"
                    }
                }
                return
            
            # 2. 更新会话状态为生成中
            self.session_service.update_session_data(session_id, {
                'status': 'generating',
                'generation_started_at': datetime.utcnow().isoformat()
            })
            
            yield {
                'type': 'status',
                'data': {
                    'status': 'generating',
                    'message': '开始生成测试用例...'
                }
            }
            
            # 3. 构建生成上下文
            context = self._build_generation_context(session_data)
            
            # 4. 调用AI服务进行流式生成
            try:
                for response in self.ai_service.generate_test_cases(session_id, context):
                    yield response
                    
                    # 如果生成完成，保存结果到会话
                    if response.get('type') == 'complete':
                        test_cases = response.get('data', {}).get('test_cases', [])
                        self.session_service.update_session_data(session_id, {
                            'status': 'generated',
                            'test_cases': test_cases,
                            'generation_completed_at': datetime.utcnow().isoformat()
                        })
                        
                        logger.info(f"测试用例生成完成: {session_id}, 共{len(test_cases)}条")
                        
            except Exception as e:
                logger.error(f"生成测试用例失败: {session_id}, {e}")
                
                # 更新会话状态为失败
                self.session_service.update_session_data(session_id, {
                    'status': 'generation_failed',
                    'error': str(e),
                    'failed_at': datetime.utcnow().isoformat()
                })
                
                yield {
                    'type': 'error',
                    'data': {
                        'error': 'generation_failed',
                        'message': '生成测试用例失败，请重试'
                    }
                }
                
        except Exception as e:
            logger.error(f"流式生成异常: {session_id}, {e}")
            yield {
                'type': 'error',
                'data': {
                    'error': 'stream_error',
                    'message': '生成过程出现异常'
                }
            }
    
    def finalize_test_cases(self, session_id: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        确认并生成最终文件
        
        Args:
            session_id: 会话ID
            test_cases: 编辑后的测试用例数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 1. 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            # 验证会话状态
            if session_data.get('status') not in ['generated', 'finalized']:
                return {
                    'success': False,
                    'error': 'invalid_status',
                    'message': f"会话状态不支持确认操作: {session_data.get('status')}"
                }
            
            # 2. 验证测试用例数据
            if not test_cases or not isinstance(test_cases, list):
                return {
                    'success': False,
                    'error': 'invalid_test_cases',
                    'message': '测试用例数据无效'
                }
            
            # 3. 生成XML文件
            try:
                xml_content = self.file_service.generate_xml_output(test_cases)
                logger.debug(f"生成XML内容成功: {session_id}")
            except Exception as e:
                logger.error(f"生成XML失败: {session_id}, {e}")
                return {
                    'success': False,
                    'error': 'xml_generation_failed',
                    'message': f'生成XML文件失败: {str(e)}'
                }
            
            # 4. 保存生成的文件
            try:
                file_info = self.file_service.save_generated_file(session_id, xml_content)
                logger.info(f"保存生成文件成功: {session_id} -> {file_info['file_id']}")
            except Exception as e:
                logger.error(f"保存生成文件失败: {session_id}, {e}")
                return {
                    'success': False,
                    'error': 'file_save_failed',
                    'message': f'保存文件失败: {str(e)}'
                }
            
            # 5. 更新会话数据
            self.session_service.update_session_data(session_id, {
                'status': 'finalized',
                'final_test_cases': test_cases,
                'generated_file_id': file_info['file_id'],
                'generated_file_path': file_info['file_path'],
                'finalized_at': datetime.utcnow().isoformat()
            })
            
            return {
                'success': True,
                'file_id': file_info['file_id'],
                'filename': file_info['filename'],
                'file_size': file_info['file_size'],
                'test_cases_count': len(test_cases),
                'message': f'成功生成包含{len(test_cases)}条测试用例的文件'
            }
            
        except Exception as e:
            logger.error(f"确认测试用例失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'finalize_failed',
                'message': '确认测试用例失败，请重试'
            }
    
    def get_generated_file(self, session_id: str, file_id: str) -> Dict[str, Any]:
        """
        获取生成的文件
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
            
        Returns:
            Dict[str, Any]: 文件信息和内容
        """
        try:
            # 1. 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            # 2. 验证文件权限
            if session_data.get('generated_file_id') != file_id:
                return {
                    'success': False,
                    'error': 'file_access_denied',
                    'message': '无权访问该文件'
                }
            
            # 3. 获取文件信息
            file_info = self.file_service.get_file_info(session_id, file_id)
            if not file_info:
                return {
                    'success': False,
                    'error': 'file_not_found',
                    'message': '文件不存在'
                }
            
            # 4. 读取文件内容
            try:
                file_content = self.file_service.get_file_content(file_info['file_path'])
                logger.info(f"获取文件成功: {session_id}/{file_id}")
            except Exception as e:
                logger.error(f"读取文件失败: {session_id}/{file_id}, {e}")
                return {
                    'success': False,
                    'error': 'file_read_failed',
                    'message': '读取文件失败'
                }
            
            return {
                'success': True,
                'file_info': file_info,
                'file_content': file_content,
                'content_type': 'application/xml'
            }
            
        except Exception as e:
            logger.error(f"获取生成文件失败: {session_id}/{file_id}, {e}")
            return {
                'success': False,
                'error': 'get_file_failed',
                'message': '获取文件失败'
            }
    
    def get_generation_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取生成状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 生成状态信息
        """
        try:
            # 验证会话有效性
            if not self.session_service.is_session_valid(session_id):
                return {
                    'success': False,
                    'error': 'session_invalid',
                    'message': '会话无效或已过期'
                }
            
            session_data = self.session_service.get_session_data(session_id)
            if not session_data:
                return {
                    'success': False,
                    'error': 'session_not_found',
                    'message': '会话数据不存在'
                }
            
            # 构建状态信息
            status_info = {
                'session_id': session_id,
                'status': session_data.get('status', 'unknown'),
                'created_at': session_data.get('created_at'),
                'updated_at': session_data.get('updated_at'),
                'files_uploaded': len(session_data.get('files', {})),
                'has_test_cases': 'test_cases' in session_data,
                'test_cases_count': len(session_data.get('test_cases', [])),
                'has_generated_file': 'generated_file_id' in session_data
            }
            
            # 添加时间戳信息
            if 'generation_started_at' in session_data:
                status_info['generation_started_at'] = session_data['generation_started_at']
            if 'generation_completed_at' in session_data:
                status_info['generation_completed_at'] = session_data['generation_completed_at']
            if 'finalized_at' in session_data:
                status_info['finalized_at'] = session_data['finalized_at']
            
            # 添加文件信息
            if session_data.get('generated_file_id'):
                status_info['generated_file_id'] = session_data['generated_file_id']
            
            return {
                'success': True,
                'status_info': status_info
            }
            
        except Exception as e:
            logger.error(f"获取生成状态失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'get_status_failed',
                'message': '获取生成状态失败'
            }
    
    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """
        清理会话资源
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        try:
            # 清理文件
            file_cleanup_success = self.file_service.cleanup_session_files(session_id)
            
            # 删除会话数据
            session_cleanup_result = self.session_service.delete_session(session_id)
            
            logger.info(f"清理会话完成: {session_id}")
            return {
                'success': True,
                'file_cleanup': file_cleanup_success,
                'session_cleanup': session_cleanup_result.get('success', False),
                'message': '会话资源清理完成'
            }
            
        except Exception as e:
            logger.error(f"清理会话失败: {session_id}, {e}")
            return {
                'success': False,
                'error': 'cleanup_failed',
                'message': '清理会话资源失败'
            }
    
    def _cleanup_failed_session(self, session_id: str) -> None:
        """
        清理失败的会话
        
        Args:
            session_id: 会话ID
        """
        try:
            self.file_service.cleanup_session_files(session_id)
            self.session_service.delete_session(session_id)
            logger.info(f"清理失败会话: {session_id}")
        except Exception as e:
            logger.error(f"清理失败会话异常: {session_id}, {e}")
    
    def _build_initial_message(self, analysis_result: Dict[str, Any]) -> str:
        """
        构建初始分析消息
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 初始消息
        """
        message_parts = ["文件分析完成！"]
        
        if analysis_result.get('template_info'):
            message_parts.append(analysis_result['template_info'])
        
        if analysis_result.get('history_info'):
            message_parts.append(analysis_result['history_info'])
        
        message_parts.append("请描述您希望生成的测试用例类型和测试场景。")
        
        return " ".join(message_parts)
    
    def _build_generation_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建生成上下文
        
        Args:
            session_data: 会话数据
            
        Returns:
            Dict[str, Any]: 生成上下文
        """
        context = {
            'session_id': session_data.get('session_id'),
            'files_info': session_data.get('files', {}),
            'config': session_data.get('config', {}),
            'analysis_result': session_data.get('analysis_result', {}),
            'chat_history': session_data.get('chat_history', []),
            'requirements': self._extract_requirements_from_chat(session_data.get('chat_history', []))
        }
        
        return context
    
    def _extract_requirements_from_chat(self, chat_history: List[Dict[str, Any]]) -> List[str]:
        """
        从对话历史中提取需求
        
        Args:
            chat_history: 对话历史
            
        Returns:
            List[str]: 提取的需求列表
        """
        requirements = []
        
        for message in chat_history:
            if message.get('role') == 'user':
                user_message = message.get('message', '').strip()
                if user_message and len(user_message) > 3:  # 过滤太短的消息，调整阈值
                    requirements.append(user_message)
        
        return requirements
    
    async def auto_analyze_and_chat(self, session_id: str, files_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动分析文件并发送给Dify (修改为以用户口吻发送) - 只发送一条消息
        
        Args:
            session_id: 会话ID
            files_info: 文件信息
            
        Returns:
            Dict[str, Any]: Dify分析结果
        """
        try:
            # 1. 解析XML文件内容（只提取第一个测试用例）
            extracted_content = self._extract_test_case_content(files_info)
            logger.info(f"提取第一个测试用例内容成功: {session_id}, 内容长度: {len(extracted_content)}")
            
            # 2. 构建以用户口吻发送给Dify的消息
            # 获取文件名
            file_name = "用例文件"
            if 'case_template' in files_info:
                file_name = files_info['case_template'].get('original_name', 
                           files_info['case_template'].get('original_filename', '用例文件'))
            
            # 以用户的口吻描述用例内容（确保只发送一条消息）
            message = f"""我上传了一个测试用例文件：{file_name}

以下是文件中第一个测试用例的内容：

{extracted_content}

请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"""
            
            # 3. 发送给AI服务（以用户身份）- 确保只调用一次
            context = {
                'files_info': files_info,
                'extracted_content': extracted_content,
                'session_id': session_id,
                'user_initiated': True,  # 标记这是用户发起的消息
                'file_name': file_name,
                'auto_analysis': True,  # 标记这是自动分析
                'single_message': True  # 确保只发送一条消息
            }
            
            logger.info(f"开始自动分析对话（以用户身份，只发送一条消息）: {session_id}")
            logger.info(f"消息内容预览: {message[:100]}...")
            
            response = await self.ai_service.chat_with_agent(session_id, message, context)
            
            if response.get('success'):
                logger.info(f"自动分析对话成功: {session_id}, conversation_id: {response.get('conversation_id', 'N/A')}")
                return response
            else:
                logger.error(f"自动分析对话失败: {session_id}, error: {response.get('error', 'unknown')}")
                return {'success': False, 'error': response.get('error', 'chat_failed')}
            
        except Exception as e:
            logger.error(f"自动分析和对话异常: {session_id}, {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
    
    def _extract_test_case_content(self, files_info: Dict[str, Any]) -> str:
        """
        从文件信息中提取测试用例内容 (新增方法)
        
        Args:
            files_info: 文件信息字典
            
        Returns:
            str: 提取的测试用例描述
        """
        if 'case_template' not in files_info:
            logger.warning("未找到case_template文件，使用默认模板")
            return self._get_default_test_case_template()
        
        try:
            file_path = files_info['case_template']['file_path']
            extracted_content = self.file_service.extract_test_case_description(file_path)
            logger.info(f"成功提取XML内容: {file_path}")
            return extracted_content
        except Exception as e:
            logger.warning(f"XML解析失败，使用默认模板: {e}")
            return self._get_default_test_case_template()
    
    def _get_default_test_case_template(self) -> str:
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