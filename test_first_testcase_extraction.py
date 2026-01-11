#!/usr/bin/env python3
"""
测试只提取第一个测试用例的功能
"""

import logging
from services.file_service import FileService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_first_testcase_extraction():
    """测试只提取第一个测试用例"""
    print("🔍 测试只提取第一个测试用例...")
    
    try:
        # 1. 初始化文件服务
        file_service = FileService('uploads')
        
        # 2. 测试中文XML文件（包含两个测试用例）
        test_file_path = 'test_case_chinese.xml'
        
        print(f"📁 解析文件: {test_file_path}")
        
        # 3. 提取测试用例描述
        extracted_content = file_service.extract_test_case_description(test_file_path)
        
        print("📝 提取的内容:")
        print("=" * 60)
        print(extracted_content)
        print("=" * 60)
        
        # 4. 验证是否只包含第一个测试用例的内容
        if "银行转账功能测试" in extracted_content:
            print("✅ 成功提取第一个测试用例（银行转账功能测试）")
        else:
            print("❌ 未找到第一个测试用例的标识")
            
        if "账户查询功能测试" in extracted_content:
            print("❌ 错误：提取了第二个测试用例（账户查询功能测试）")
            return False
        else:
            print("✅ 成功：没有提取第二个测试用例")
        
        # 5. 检查关键内容
        expected_keywords = [
            "CBS系统运行正常",
            "登录CBS系统",
            "转账操作成功",
            "account_balance表amount字段值为80"
        ]
        
        missing_keywords = []
        for keyword in expected_keywords:
            if keyword not in extracted_content:
                missing_keywords.append(keyword)
        
        if missing_keywords:
            print(f"❌ 缺少关键内容: {missing_keywords}")
            return False
        else:
            print("✅ 包含所有预期的关键内容")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_generation_service():
    """测试与GenerationService的集成"""
    print("\n🔗 测试与GenerationService的集成...")
    
    try:
        from services.generation_service import GenerationService
        from services.session_service import SessionService
        from services.ai_service import AIService
        from config import Config
        from werkzeug.datastructures import FileStorage
        import io
        
        # 1. 初始化服务
        session_service = SessionService(None)  # 使用内存存储
        file_service = FileService('uploads')
        ai_config = Config.AI_SERVICE_CONFIG.copy()
        ai_service = AIService(ai_config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        # 2. 读取测试文件内容
        with open('test_case_chinese.xml', 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 3. 创建模拟的FileStorage对象
        file_storage = FileStorage(
            stream=io.BytesIO(xml_content.encode('utf-8')),
            filename='test_case_chinese.xml',
            content_type='application/xml'
        )
        
        files = {
            'case_template': file_storage
        }
        
        config = {}
        
        # 4. 测试提取内容
        print("🚀 测试GenerationService中的内容提取...")
        
        # 模拟文件保存后的files_info结构
        files_info = {
            'case_template': {
                'file_id': 'test_file_001',
                'original_filename': 'test_case_chinese.xml',
                'file_path': 'test_case_chinese.xml',
                'file_size': len(xml_content)
            }
        }
        
        # 5. 调用提取方法
        extracted_content = generation_service._extract_test_case_content(files_info)
        
        print("📝 GenerationService提取的内容:")
        print("=" * 60)
        print(extracted_content)
        print("=" * 60)
        
        # 6. 验证结果
        if "银行转账功能测试" in extracted_content and "账户查询功能测试" not in extracted_content:
            print("✅ GenerationService成功只提取第一个测试用例")
            return True
        else:
            print("❌ GenerationService提取结果不正确")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("测试只提取第一个测试用例的功能")
    print("=" * 60)
    
    # 1. 测试文件服务的提取功能
    file_service_result = test_first_testcase_extraction()
    
    # 2. 测试与GenerationService的集成
    integration_result = test_with_generation_service()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print(f"✅ 文件服务提取: {'成功' if file_service_result else '失败'}")
    print(f"✅ 集成测试: {'成功' if integration_result else '失败'}")
    
    if file_service_result and integration_result:
        print("\n🎉 所有测试通过！现在只会提取第一个测试用例。")
        print("系统将只发送第一个测试用例给Dify，避免多次请求。")
    else:
        print("\n❌ 部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    main()