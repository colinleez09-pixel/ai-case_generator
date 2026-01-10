import pytest
from services.config_service import ConfigService


class TestConfigService:
    """配置服务单元测试"""
    
    @pytest.fixture
    def config_service(self):
        """创建配置服务实例"""
        return ConfigService()
    
    def test_init(self):
        """测试初始化"""
        service = ConfigService()
        assert service._api_versions is not None
        assert service._preset_steps is not None
        assert service._preset_components is not None
        assert len(service._api_versions) > 0
        assert len(service._preset_steps) > 0
        assert len(service._preset_components) > 0
    
    def test_get_api_versions_success(self, config_service):
        """测试成功获取API版本列表"""
        result = config_service.get_api_versions()
        
        assert result['success'] is True
        assert 'versions' in result
        assert isinstance(result['versions'], list)
        assert len(result['versions']) > 0
        
        # 验证版本格式
        for version in result['versions']:
            assert 'value' in version
            assert 'label' in version
            assert isinstance(version['value'], str)
            assert isinstance(version['label'], str)
    
    def test_get_api_versions_content(self, config_service):
        """测试API版本列表内容"""
        result = config_service.get_api_versions()
        versions = result['versions']
        
        # 验证包含预期的版本
        version_values = [v['value'] for v in versions]
        assert 'v1.0' in version_values
        assert 'v2.0' in version_values
        assert 'v2.1' in version_values
        
        # 验证标签格式
        for version in versions:
            assert 'API' in version['label']
            assert '(' in version['label'] and ')' in version['label']
    
    def test_get_preset_steps_success(self, config_service):
        """测试成功获取预设步骤列表"""
        result = config_service.get_preset_steps()
        
        assert result['success'] is True
        assert 'steps' in result
        assert isinstance(result['steps'], list)
        assert len(result['steps']) > 0
        
        # 验证步骤格式
        for step in result['steps']:
            assert 'id' in step
            assert 'name' in step
            assert 'description' in step
            assert 'category' in step
            assert 'components' in step
            assert isinstance(step['components'], list)
    
    def test_get_preset_steps_content(self, config_service):
        """测试预设步骤列表内容"""
        result = config_service.get_preset_steps()
        steps = result['steps']
        
        # 验证包含预期的步骤
        step_names = [s['name'] for s in steps]
        assert '打开登录页面' in step_names
        assert '输入用户名' in step_names
        assert '输入密码' in step_names
        assert '点击登录按钮' in step_names
        assert '验证登录状态' in step_names
        
        # 验证步骤分类
        categories = set(s['category'] for s in steps)
        expected_categories = {'navigation', 'input', 'action', 'validation'}
        assert expected_categories.issubset(categories)
        
        # 验证组件结构
        for step in steps:
            for component in step['components']:
                assert 'type' in component
                assert 'name' in component
                assert 'params' in component
                assert isinstance(component['params'], dict)
    
    def test_get_preset_components_success(self, config_service):
        """测试成功获取预设组件列表"""
        result = config_service.get_preset_components()
        
        assert result['success'] is True
        assert 'components' in result
        assert isinstance(result['components'], list)
        assert len(result['components']) > 0
        
        # 验证组件格式
        for component in result['components']:
            assert 'id' in component
            assert 'type' in component
            assert 'name' in component
            assert 'icon' in component
            assert 'description' in component
            assert 'default_params' in component
            assert isinstance(component['default_params'], dict)
    
    def test_get_preset_components_content(self, config_service):
        """测试预设组件列表内容"""
        result = config_service.get_preset_components()
        components = result['components']
        
        # 验证包含预期的组件类型
        component_types = [c['type'] for c in components]
        expected_types = ['input', 'button', 'select', 'checkbox', 'radio', 'api', 'assert', 'wait', 'screenshot', 'log']
        for expected_type in expected_types:
            assert expected_type in component_types
        
        # 验证组件名称
        component_names = [c['name'] for c in components]
        assert '输入框' in component_names
        assert '按钮' in component_names
        assert '接口调用' in component_names
        assert '断言验证' in component_names
        
        # 验证默认参数结构
        for component in components:
            default_params = component['default_params']
            assert len(default_params) > 0
            
            # 验证特定组件的参数
            if component['type'] == 'input':
                assert 'selector' in default_params
                assert 'value' in default_params
            elif component['type'] == 'api':
                assert 'method' in default_params
                assert 'url' in default_params
            elif component['type'] == 'assert':
                assert 'type' in default_params
                assert 'expected' in default_params
    
    def test_get_all_config_success(self, config_service):
        """测试成功获取所有配置"""
        result = config_service.get_all_config()
        
        assert result['success'] is True
        assert 'config' in result
        
        config = result['config']
        assert 'api_versions' in config
        assert 'preset_steps' in config
        assert 'preset_components' in config
        
        # 验证数据一致性
        assert config['api_versions'] == config_service._api_versions
        assert config['preset_steps'] == config_service._preset_steps
        assert config['preset_components'] == config_service._preset_components
    
    def test_api_versions_structure(self, config_service):
        """测试API版本数据结构"""
        versions = config_service._api_versions
        
        for version in versions:
            # 验证必需字段
            assert 'value' in version
            assert 'label' in version
            
            # 验证数据类型
            assert isinstance(version['value'], str)
            assert isinstance(version['label'], str)
            
            # 验证格式
            assert len(version['value']) > 0
            assert len(version['label']) > 0
            assert version['value'].startswith('v')
    
    def test_preset_steps_structure(self, config_service):
        """测试预设步骤数据结构"""
        steps = config_service._preset_steps
        
        for step in steps:
            # 验证必需字段
            required_fields = ['id', 'name', 'description', 'category', 'components']
            for field in required_fields:
                assert field in step
            
            # 验证数据类型
            assert isinstance(step['id'], str)
            assert isinstance(step['name'], str)
            assert isinstance(step['description'], str)
            assert isinstance(step['category'], str)
            assert isinstance(step['components'], list)
            
            # 验证组件结构
            for component in step['components']:
                assert 'type' in component
                assert 'name' in component
                assert 'params' in component
                assert isinstance(component['params'], dict)
    
    def test_preset_components_structure(self, config_service):
        """测试预设组件数据结构"""
        components = config_service._preset_components
        
        for component in components:
            # 验证必需字段
            required_fields = ['id', 'type', 'name', 'icon', 'description', 'default_params']
            for field in required_fields:
                assert field in component
            
            # 验证数据类型
            assert isinstance(component['id'], str)
            assert isinstance(component['type'], str)
            assert isinstance(component['name'], str)
            assert isinstance(component['icon'], str)
            assert isinstance(component['description'], str)
            assert isinstance(component['default_params'], dict)
            
            # 验证ID格式
            assert component['id'].startswith('comp_')
    
    def test_component_categories_coverage(self, config_service):
        """测试组件类型覆盖度"""
        components = config_service._preset_components
        component_types = set(c['type'] for c in components)
        
        # 验证覆盖了主要的组件类型
        essential_types = {
            'input',    # 输入组件
            'button',   # 按钮组件
            'select',   # 选择组件
            'api',      # API调用
            'assert',   # 断言验证
            'wait'      # 等待操作
        }
        
        assert essential_types.issubset(component_types)
    
    def test_step_categories_coverage(self, config_service):
        """测试步骤分类覆盖度"""
        steps = config_service._preset_steps
        categories = set(s['category'] for s in steps)
        
        # 验证覆盖了主要的步骤分类
        essential_categories = {
            'navigation',   # 导航操作
            'input',        # 输入操作
            'action',       # 动作操作
            'validation'    # 验证操作
        }
        
        assert essential_categories.issubset(categories)
    
    def test_login_workflow_steps(self, config_service):
        """测试登录工作流步骤完整性"""
        steps = config_service._preset_steps
        step_names = [s['name'] for s in steps]
        
        # 验证登录流程的关键步骤都存在
        login_steps = [
            '打开登录页面',
            '输入用户名',
            '输入密码',
            '点击登录按钮',
            '验证登录状态'
        ]
        
        for login_step in login_steps:
            assert login_step in step_names
    
    def test_search_workflow_steps(self, config_service):
        """测试搜索工作流步骤完整性"""
        steps = config_service._preset_steps
        step_names = [s['name'] for s in steps]
        
        # 验证搜索流程的关键步骤都存在
        search_steps = [
            '打开搜索页面',
            '输入搜索关键词',
            '点击搜索按钮',
            '验证搜索结果'
        ]
        
        for search_step in search_steps:
            assert search_step in step_names
    
    def test_component_default_params_completeness(self, config_service):
        """测试组件默认参数完整性"""
        components = config_service._preset_components
        
        for component in components:
            default_params = component['default_params']
            component_type = component['type']
            
            # 根据组件类型验证必需的默认参数
            if component_type == 'input':
                required_params = ['selector', 'value']
                for param in required_params:
                    assert param in default_params
            
            elif component_type == 'button':
                required_params = ['selector', 'action']
                for param in required_params:
                    assert param in default_params
            
            elif component_type == 'api':
                required_params = ['method', 'url']
                for param in required_params:
                    assert param in default_params
            
            elif component_type == 'assert':
                required_params = ['type', 'expected']
                for param in required_params:
                    assert param in default_params


class TestConfigServiceErrorHandling:
    """配置服务错误处理测试"""
    
    @pytest.fixture
    def config_service(self):
        """创建配置服务实例"""
        return ConfigService()
    
    def test_get_api_versions_exception_handling(self, config_service):
        """测试获取API版本异常处理"""
        # 这个测试主要验证方法的健壮性
        # 在正常情况下，配置服务应该能正常工作
        result = config_service.get_api_versions()
        assert result['success'] is True
    
    def test_data_consistency(self, config_service):
        """测试数据一致性"""
        # 多次调用应该返回相同的数据
        result1 = config_service.get_api_versions()
        result2 = config_service.get_api_versions()
        
        assert result1 == result2
        
        result1 = config_service.get_preset_steps()
        result2 = config_service.get_preset_steps()
        
        assert result1 == result2
        
        result1 = config_service.get_preset_components()
        result2 = config_service.get_preset_components()
        
        assert result1 == result2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])