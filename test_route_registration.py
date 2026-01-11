#!/usr/bin/env python3
"""
测试路由注册

检查流式聊天路由是否正确注册到Flask应用中。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_route_registration():
    """测试路由注册"""
    print("🧪 测试路由注册...")
    
    try:
        # 创建应用实例
        app = create_app()
        
        print("📋 已注册的路由:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.methods} {rule.rule}")
        
        # 检查特定路由
        streaming_support_found = False
        streaming_chat_found = False
        
        for rule in app.url_map.iter_rules():
            if '/api/chat/streaming/support' in rule.rule:
                streaming_support_found = True
                print(f"✅ 找到流式支持检查路由: {rule.methods} {rule.rule}")
            
            if '/api/chat/stream' in rule.rule:
                streaming_chat_found = True
                print(f"✅ 找到流式聊天路由: {rule.methods} {rule.rule}")
        
        if not streaming_support_found:
            print("❌ 未找到流式支持检查路由")
        
        if not streaming_chat_found:
            print("❌ 未找到流式聊天路由")
        
        # 测试应用上下文
        with app.app_context():
            print("✅ 应用上下文正常")
            
            # 检查配置
            if hasattr(app, 'config') and 'AI_SERVICE_CONFIG' in app.config:
                print("✅ AI服务配置存在")
            else:
                print("⚠️  AI服务配置缺失")
            
            # 检查Redis连接
            if hasattr(app, 'redis') and app.redis:
                print("✅ Redis连接正常")
            else:
                print("⚠️  Redis连接缺失")
        
        return streaming_support_found and streaming_chat_found
        
    except Exception as e:
        print(f"❌ 路由注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_dependencies():
    """测试依赖导入"""
    print("\n🧪 测试依赖导入...")
    
    try:
        from services.streaming_chat_handler import StreamingChatHandler
        print("✅ StreamingChatHandler导入成功")
    except Exception as e:
        print(f"❌ StreamingChatHandler导入失败: {e}")
        return False
    
    try:
        from services.ai_service import AIService
        print("✅ AIService导入成功")
    except Exception as e:
        print(f"❌ AIService导入失败: {e}")
        return False
    
    try:
        from services.chat_service import ChatService
        print("✅ ChatService导入成功")
    except Exception as e:
        print(f"❌ ChatService导入失败: {e}")
        return False
    
    try:
        from services.session_service import SessionService
        print("✅ SessionService导入成功")
    except Exception as e:
        print(f"❌ SessionService导入失败: {e}")
        return False
    
    return True

def test_streaming_handler_creation():
    """测试流式处理器创建"""
    print("\n🧪 测试流式处理器创建...")
    
    try:
        from services.ai_service import AIService
        from services.streaming_chat_handler import StreamingChatHandler
        
        # 创建AI服务配置
        config = {
            'mock_mode': True,
            'dify_url': 'https://api.dify.ai/v1',
            'dify_token': 'test_token',
            'timeout': 30
        }
        
        # 创建AI服务
        ai_service = AIService(config)
        print("✅ AI服务创建成功")
        
        # 创建流式处理器
        streaming_handler = StreamingChatHandler(ai_service)
        print("✅ 流式处理器创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 流式处理器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("🚀 开始路由注册测试\n")
    print("=" * 60)
    
    # 测试1: 依赖导入
    import_success = test_import_dependencies()
    
    # 测试2: 流式处理器创建
    handler_success = test_streaming_handler_creation()
    
    # 测试3: 路由注册
    route_success = test_route_registration()
    
    print("\n" + "=" * 60)
    print("📝 测试总结:")
    print(f"✅ 依赖导入: {'通过' if import_success else '失败'}")
    print(f"✅ 处理器创建: {'通过' if handler_success else '失败'}")
    print(f"✅ 路由注册: {'通过' if route_success else '失败'}")
    
    if all([import_success, handler_success, route_success]):
        print("\n🎉 所有测试通过！流式聊天功能应该可以正常工作。")
    else:
        print("\n⚠️  部分测试失败，需要检查相关问题。")

if __name__ == "__main__":
    main()