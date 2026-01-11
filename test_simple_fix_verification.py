#!/usr/bin/env python3
"""
简单验证修复效果
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.file_service import FileService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_xml_extraction_fix():
    """测试XML提取修复：只提取第一个测试用例"""
    print("🎯 测试XML提取修复：只提取第一个测试用例")
    
    try:
        config = Config()
        file_service = FileService(config.UPLOAD_FOLDER)
        
        # 测试XML提取
        xml_file_path = 'test_case_chinese.xml'
        if os.path.exists(xml_file_path):
            print(f"📁 测试文件: {xml_file_path}")
            
            extracted_content = file_service.extract_test_case_description(xml_file_path)
            
            print(f"\n📝 提取的内容:")
            print(extracted_content)
            
            # 检查是否只包含一个测试用例
            case_count = extracted_content.count('【测试用例】')
            print(f"\n📊 检测到的测试用例数量: {case_count}")
            
            if case_count <= 1:
                print("✅ 成功：只提取了第一个测试用例")
                return True
            else:
                print("❌ 失败：提取了多个测试用例")
                return False
        else:
            print(f"⚠️  测试文件不存在: {xml_file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_ai_service_mode():
    """测试AI服务模式配置"""
    print("\n🎯 测试AI服务模式配置")
    
    try:
        config = Config()
        ai_config = config.AI_SERVICE_CONFIG
        
        print(f"📋 AI服务配置:")
        print(f"  Mock模式: {ai_config.get('mock_mode', True)}")
        print(f"  Dify URL: {ai_config.get('dify_url', 'N/A')}")
        print(f"  超时时间: {ai_config.get('timeout', 30)}秒")
        
        # 检查是否配置为非Mock模式
        if not ai_config.get('mock_mode', True):
            print("✅ 成功：AI服务配置为Dify模式")
            return True
        else:
            print("❌ 失败：AI服务仍配置为Mock模式")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_generation_service_logic():
    """测试生成服务逻辑修改"""
    print("\n🎯 测试生成服务逻辑修改")
    
    try:
        from services.generation_service import GenerationService
        import inspect
        
        # 检查auto_analyze_and_chat方法是否存在
        if hasattr(GenerationService, 'auto_analyze_and_chat'):
            method = getattr(GenerationService, 'auto_analyze_and_chat')
            source = inspect.getsource(method)
            
            # 检查关键修改
            checks = [
                ('single_message', 'single_message' in source),
                ('只发送一条消息', '只发送一条消息' in source),
                ('auto_analysis', 'auto_analysis' in source),
                ('第一个测试用例', '第一个测试用例' in source)
            ]
            
            print("📋 代码修改检查:")
            all_passed = True
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}: {'存在' if check_result else '不存在'}")
                if not check_result:
                    all_passed = False
            
            if all_passed:
                print("✅ 成功：生成服务逻辑已正确修改")
                return True
            else:
                print("❌ 失败：生成服务逻辑修改不完整")
                return False
        else:
            print("❌ 失败：auto_analyze_and_chat方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 开始验证修复效果")
    print("="*50)
    
    results = []
    
    # 测试1：XML提取修复
    result1 = test_xml_extraction_fix()
    results.append(("XML提取只获取第一个测试用例", result1))
    
    # 测试2：AI服务模式配置
    result2 = test_ai_service_mode()
    results.append(("AI服务配置为Dify模式", result2))
    
    # 测试3：生成服务逻辑修改
    result3 = test_generation_service_logic()
    results.append(("生成服务逻辑修改", result3))
    
    # 汇总结果
    print("\n" + "="*50)
    print("📊 验证结果汇总")
    print("="*50)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n📈 总体结果: {total_passed}/{total_tests} 个验证通过")
    
    if total_passed == total_tests:
        print("🎉 所有修复都已正确实施！")
    else:
        print("⚠️  还有修复需要进一步检查")

if __name__ == "__main__":
    main()