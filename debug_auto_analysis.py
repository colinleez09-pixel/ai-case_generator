#!/usr/bin/env python3
"""
调试自动分析功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载Dify连接补丁
try:
    import dify_patch
    print("✅ Dify连接补丁已加载")
except ImportError:
    print("⚠️ Dify连接补丁未找到")

from services.ai_service import AIService
from services.generation_service import GenerationService
from services.file_service import FileService
from services.session_service import SessionService
from config import Config

async def debug_auto_analysis():
    """调试自动分析功能"""
    print("🔍 调试自动分析功能...")
    
    try:
        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # 初始化服务
        config = Config.AI_SERVICE_CONFIG.copy()
        print(f"📊 配置状态: mock_mode={config['mock_mode']}")
        
        upload_folder = Config().UPLOAD_FOLDER
        file_service = FileService(upload_folder)
        session_service = SessionService(redis_client=None)
        ai_service = AIService(config)
        generation_service = GenerationService(file_service, session_service, ai_service)
        
        print(f"📊 AI服务模式: {ai_service.mode_selector.current_mode}")
        print(f"📊 是否Mock模式: {ai_service.mode_selector.is_mock_mode()}")
        
        # 1. 测试文件分析
        print("\n📊 测试文件分析...")
        
        mock_files_info = {
            'case_template': {
                'file_id': 'test_file_001',
                'original_filename': 'cbs_test_case.xml',
                'file_path': 'test_case_simple.xml',
                'file_size': 1024,
                'upload_time': datetime.utcnow().isoformat()
            }
        }
        
        analysis_result = ai_service.analyze_files(mock_files_info)
        print(f"📝 文件分析结果:")
        print(f"  成功: {analysis_result.get('success', False)}")
        print(f"  模板信息: {analysis_result.get('template_info', '无')}")
        
        # 2. 测试自动分析和对话
        if analysis_result.get('success'):
            print("\n🤖 测试自动分析和对话...")
            
            session_id = 'debug_session_001'
            auto_result = await generation_service.auto_analyze_and_chat(session_id, mock_files_info)
            
            print(f"📝 自动分析结果:")
            print(f"  成功: {auto_result.get('success', False)}")
            print(f"  回复: {auto_result.get('reply', '无回复')[:200]}...")
            print(f"  对话ID: {auto_result.get('conversation_id', '无')}")
            print(f"  错误: {auto_result.get('error', '无')}")
            
            return auto_result.get('success', False)
        else:
            print("❌ 文件分析失败，无法继续测试自动分析")
            return False
            
    except Exception as e:
        print(f"❌ 调试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dify_direct_call():
    """测试直接调用Dify"""
    print("\n🚀 测试直接调用Dify...")
    
    try:
        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        config = Config.AI_SERVICE_CONFIG.copy()
        ai_service = AIService(config)
        
        session_id = 'direct_test_001'
        message = """我上传了一个测试用例文件：cbs_test_case.xml

以下是文件中的测试用例内容：

【预置条件】
1. CBS系统运行正常
2. 修改系统变量SYS_abc的值为12
3. 设置变量，初始金额为100

【测试步骤】
1. 登录CBS系统
2. 进入调账功能模块
3. 进行调账，调减20元
4. 确认调账操作

【预期结果】
1. 调账成功
2. account_balance表amount字段值为80
3. 系统显示调账成功消息

请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。"""
        
        context = {
            'user_initiated': True,
            'file_name': 'cbs_test_case.xml'
        }
        
        print("📤 发送消息到Dify...")
        result = await ai_service.chat_with_agent(session_id, message, context)
        
        print(f"📝 Dify响应:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  回复: {result.get('reply', '无回复')[:300]}...")
        print(f"  对话ID: {result.get('conversation_id', '无')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 直接调用Dify异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("调试自动分析功能")
    print("=" * 60)
    
    # 测试1: 调试自动分析
    test1_success = await debug_auto_analysis()
    
    # 测试2: 直接调用Dify
    test2_success = await test_dify_direct_call()
    
    print("\n" + "=" * 60)
    print("调试结果总结")
    print("=" * 60)
    
    print(f"✅ 自动分析功能: {'成功' if test1_success else '失败'}")
    print(f"✅ 直接Dify调用: {'成功' if test2_success else '失败'}")
    
    if test1_success and test2_success:
        print("\n🎉 自动分析功能正常！")
    else:
        print("\n⚠️ 存在问题，需要进一步调试")
    
    return test1_success and test2_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)