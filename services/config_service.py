import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ConfigService:
    """配置服务 - 管理API版本、预设步骤、预设组件等配置数据"""
    
    def __init__(self):
        """初始化配置服务"""
        self._api_versions = self._load_api_versions()
        self._preset_steps = self._load_preset_steps()
        self._preset_components = self._load_preset_components()
        
        logger.info("配置服务初始化完成")
    
    def get_api_versions(self) -> Dict[str, Any]:
        """
        获取API版本列表
        
        Returns:
            Dict[str, Any]: API版本列表
        """
        try:
            return {
                'success': True,
                'versions': self._api_versions
            }
        except Exception as e:
            logger.error(f"获取API版本失败: {e}")
            return {
                'success': False,
                'error': 'get_versions_failed',
                'message': '获取API版本列表失败'
            }
    
    def get_preset_steps(self) -> Dict[str, Any]:
        """
        获取预设步骤列表
        
        Returns:
            Dict[str, Any]: 预设步骤列表
        """
        try:
            return {
                'success': True,
                'steps': self._preset_steps
            }
        except Exception as e:
            logger.error(f"获取预设步骤失败: {e}")
            return {
                'success': False,
                'error': 'get_steps_failed',
                'message': '获取预设步骤列表失败'
            }
    
    def get_preset_components(self) -> Dict[str, Any]:
        """
        获取预设组件列表
        
        Returns:
            Dict[str, Any]: 预设组件列表
        """
        try:
            return {
                'success': True,
                'components': self._preset_components
            }
        except Exception as e:
            logger.error(f"获取预设组件失败: {e}")
            return {
                'success': False,
                'error': 'get_components_failed',
                'message': '获取预设组件列表失败'
            }
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置数据
        
        Returns:
            Dict[str, Any]: 所有配置数据
        """
        try:
            return {
                'success': True,
                'config': {
                    'api_versions': self._api_versions,
                    'preset_steps': self._preset_steps,
                    'preset_components': self._preset_components
                }
            }
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return {
                'success': False,
                'error': 'get_all_config_failed',
                'message': '获取配置数据失败'
            }
    
    def _load_api_versions(self) -> List[Dict[str, str]]:
        """
        加载API版本配置
        
        Returns:
            List[Dict[str, str]]: API版本列表
        """
        return [
            {
                "value": "v1.0",
                "label": "API v1.0 (2024-01)"
            },
            {
                "value": "v1.5",
                "label": "API v1.5 (2024-06)"
            },
            {
                "value": "v2.0",
                "label": "API v2.0 (2024-12)"
            },
            {
                "value": "v2.1",
                "label": "API v2.1 (2025-01)"
            }
        ]
    
    def _load_preset_steps(self) -> List[Dict[str, Any]]:
        """
        加载预设步骤配置
        
        Returns:
            List[Dict[str, Any]]: 预设步骤列表
        """
        return [
            {
                "id": "preset_step_1",
                "name": "打开登录页面",
                "description": "打开系统登录页面并等待加载完成",
                "category": "navigation",
                "components": [
                    {
                        "type": "api",
                        "name": "接口调用 - 获取登录页",
                        "params": {
                            "method": "GET",
                            "url": "/login"
                        }
                    },
                    {
                        "type": "assert",
                        "name": "断言 - 页面加载完成",
                        "params": {
                            "type": "exists",
                            "expected": "#login-form"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_2",
                "name": "输入用户名",
                "description": "在用户名输入框中输入测试用户名",
                "category": "input",
                "components": [
                    {
                        "type": "input",
                        "name": "输入用户名",
                        "params": {
                            "selector": "#username",
                            "value": "testuser",
                            "clear": True
                        }
                    }
                ]
            },
            {
                "id": "preset_step_3",
                "name": "输入密码",
                "description": "在密码输入框中输入测试密码",
                "category": "input",
                "components": [
                    {
                        "type": "input",
                        "name": "输入密码",
                        "params": {
                            "selector": "#password",
                            "value": "password123",
                            "clear": True,
                            "secure": True
                        }
                    }
                ]
            },
            {
                "id": "preset_step_4",
                "name": "点击登录按钮",
                "description": "点击登录按钮提交登录表单",
                "category": "action",
                "components": [
                    {
                        "type": "button",
                        "name": "点击登录",
                        "params": {
                            "selector": "#login-btn",
                            "action": "click",
                            "wait_after": 2000
                        }
                    }
                ]
            },
            {
                "id": "preset_step_5",
                "name": "验证登录状态",
                "description": "验证用户是否成功登录系统",
                "category": "validation",
                "components": [
                    {
                        "type": "assert",
                        "name": "断言 - URL跳转正确",
                        "params": {
                            "type": "equals",
                            "expected": "/dashboard"
                        }
                    },
                    {
                        "type": "assert",
                        "name": "断言 - 用户信息显示",
                        "params": {
                            "type": "exists",
                            "expected": ".user-info"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_6",
                "name": "打开搜索页面",
                "description": "导航到搜索功能页面",
                "category": "navigation",
                "components": [
                    {
                        "type": "api",
                        "name": "接口调用 - 获取搜索页",
                        "params": {
                            "method": "GET",
                            "url": "/search"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_7",
                "name": "输入搜索关键词",
                "description": "在搜索框中输入搜索关键词",
                "category": "input",
                "components": [
                    {
                        "type": "input",
                        "name": "输入搜索词",
                        "params": {
                            "selector": "#search-input",
                            "value": "测试关键词",
                            "clear": True
                        }
                    }
                ]
            },
            {
                "id": "preset_step_8",
                "name": "点击搜索按钮",
                "description": "执行搜索操作",
                "category": "action",
                "components": [
                    {
                        "type": "button",
                        "name": "点击搜索",
                        "params": {
                            "selector": "#search-btn",
                            "action": "click",
                            "wait_after": 1000
                        }
                    }
                ]
            },
            {
                "id": "preset_step_9",
                "name": "验证搜索结果",
                "description": "验证搜索结果是否正确显示",
                "category": "validation",
                "components": [
                    {
                        "type": "assert",
                        "name": "断言 - 结果列表存在",
                        "params": {
                            "type": "exists",
                            "expected": ".search-results"
                        }
                    },
                    {
                        "type": "assert",
                        "name": "断言 - 结果数量大于0",
                        "params": {
                            "type": "greater_than",
                            "expected": 0
                        }
                    }
                ]
            },
            {
                "id": "preset_step_10",
                "name": "添加商品到购物车",
                "description": "将选中的商品添加到购物车",
                "category": "action",
                "components": [
                    {
                        "type": "button",
                        "name": "点击添加到购物车",
                        "params": {
                            "selector": ".add-to-cart-btn",
                            "action": "click"
                        }
                    },
                    {
                        "type": "assert",
                        "name": "断言 - 添加成功提示",
                        "params": {
                            "type": "contains",
                            "expected": "添加成功"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_11",
                "name": "打开购物车页面",
                "description": "导航到购物车页面查看商品",
                "category": "navigation",
                "components": [
                    {
                        "type": "api",
                        "name": "接口调用 - 获取购物车",
                        "params": {
                            "method": "GET",
                            "url": "/cart"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_12",
                "name": "修改商品数量",
                "description": "修改购物车中商品的数量",
                "category": "input",
                "components": [
                    {
                        "type": "input",
                        "name": "修改数量",
                        "params": {
                            "selector": ".quantity-input",
                            "value": "2",
                            "clear": True
                        }
                    },
                    {
                        "type": "button",
                        "name": "确认修改",
                        "params": {
                            "selector": ".update-quantity-btn",
                            "action": "click"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_13",
                "name": "删除购物车商品",
                "description": "从购物车中删除指定商品",
                "category": "action",
                "components": [
                    {
                        "type": "button",
                        "name": "点击删除",
                        "params": {
                            "selector": ".remove-item-btn",
                            "action": "click"
                        }
                    },
                    {
                        "type": "button",
                        "name": "确认删除",
                        "params": {
                            "selector": ".confirm-remove-btn",
                            "action": "click"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_14",
                "name": "提交订单",
                "description": "提交购物车中的商品订单",
                "category": "action",
                "components": [
                    {
                        "type": "button",
                        "name": "点击提交订单",
                        "params": {
                            "selector": "#submit-order-btn",
                            "action": "click"
                        }
                    }
                ]
            },
            {
                "id": "preset_step_15",
                "name": "验证订单状态",
                "description": "验证订单是否成功提交",
                "category": "validation",
                "components": [
                    {
                        "type": "assert",
                        "name": "断言 - 订单成功页面",
                        "params": {
                            "type": "contains",
                            "expected": "订单提交成功"
                        }
                    },
                    {
                        "type": "assert",
                        "name": "断言 - 订单号存在",
                        "params": {
                            "type": "exists",
                            "expected": ".order-number"
                        }
                    }
                ]
            }
        ]
    
    def _load_preset_components(self) -> List[Dict[str, Any]]:
        """
        加载预设组件配置
        
        Returns:
            List[Dict[str, Any]]: 预设组件列表
        """
        return [
            {
                "id": "comp_input",
                "type": "input",
                "name": "输入框",
                "icon": "edit",
                "description": "文本输入组件",
                "default_params": {
                    "selector": "",
                    "value": "",
                    "clear": True,
                    "validation": "text",
                    "maxLength": 100
                }
            },
            {
                "id": "comp_button",
                "type": "button",
                "name": "按钮",
                "icon": "pointer",
                "description": "点击操作组件",
                "default_params": {
                    "selector": "",
                    "action": "click",
                    "wait_after": 1000,
                    "double_click": False
                }
            },
            {
                "id": "comp_select",
                "type": "select",
                "name": "下拉选择",
                "icon": "list",
                "description": "下拉选择组件",
                "default_params": {
                    "selector": "",
                    "value": "",
                    "by_text": True,
                    "multiple": False
                }
            },
            {
                "id": "comp_checkbox",
                "type": "checkbox",
                "name": "复选框",
                "icon": "check",
                "description": "勾选操作组件",
                "default_params": {
                    "selector": "",
                    "checked": True,
                    "label": "复选框标签"
                }
            },
            {
                "id": "comp_radio",
                "type": "radio",
                "name": "单选框",
                "icon": "radio",
                "description": "单选操作组件",
                "default_params": {
                    "selector": "",
                    "value": "",
                    "label": "单选框标签"
                }
            },
            {
                "id": "comp_api",
                "type": "api",
                "name": "接口调用",
                "icon": "api",
                "description": "HTTP接口请求",
                "default_params": {
                    "method": "GET",
                    "url": "/api/endpoint",
                    "headers": {},
                    "body": {},
                    "timeout": 30000
                }
            },
            {
                "id": "comp_assert",
                "type": "assert",
                "name": "断言验证",
                "icon": "check-circle",
                "description": "结果验证组件",
                "default_params": {
                    "type": "equals",
                    "expected": "",
                    "timeout": 5000,
                    "message": "断言失败"
                }
            },
            {
                "id": "comp_wait",
                "type": "wait",
                "name": "等待操作",
                "icon": "clock",
                "description": "等待指定时间或条件",
                "default_params": {
                    "type": "time",
                    "duration": 1000,
                    "condition": "",
                    "timeout": 10000
                }
            },
            {
                "id": "comp_screenshot",
                "type": "screenshot",
                "name": "截图",
                "icon": "camera",
                "description": "截取当前页面截图",
                "default_params": {
                    "filename": "screenshot.png",
                    "full_page": True,
                    "element": ""
                }
            },
            {
                "id": "comp_log",
                "type": "log",
                "name": "日志输出",
                "icon": "file-text",
                "description": "输出日志信息",
                "default_params": {
                    "level": "info",
                    "message": "日志信息",
                    "data": {}
                }
            }
        ]