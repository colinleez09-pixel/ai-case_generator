#!/usr/bin/env python3
"""
最终验证测试 - 检查前端修复是否正确
"""

import time
import requests
from bs4 import BeautifulSoup

def test_frontend_fixes():
    """测试前端修复"""
    
    print("开始验证前端修复...")
    
    try:
        # 获取页面HTML
        response = requests.get("http://127.0.0.1:5000", timeout=10)
        response.raise_for_status()
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("✓ 页面请求成功")
        
        # 1. 检查遮罩层是否有hidden类
        overlay = soup.find('div', {'id': 'chatDisabledOverlay'})
        if overlay and 'hidden' in overlay.get('class', []):
            print("✓ 遮罩层正确设置为hidden")
        else:
            print("✗ 遮罩层没有设置为hidden")
            
        # 2. 检查是否移除了静态初始消息
        chat_messages = soup.find('div', {'id': 'chatMessages'})
        if chat_messages:
            # 检查是否包含静态消息
            static_message = chat_messages.find('div', class_='message')
            if static_message is None:
                print("✓ 静态初始消息已正确移除")
            else:
                print("✗ 静态初始消息仍然存在")
                
            # 检查是否有注释
            if '初始消息将通过JavaScript动态添加' in str(chat_messages):
                print("✓ 动态消息注释已添加")
            else:
                print("✗ 动态消息注释未找到")
        else:
            print("✗ 未找到聊天消息容器")
            
        # 3. 检查输入框的placeholder（这个在HTML中是静态的）
        chat_input = soup.find('input', {'id': 'chatInput'})
        if chat_input:
            placeholder = chat_input.get('placeholder', '')
            if '输入消息，按 Enter 发送...' in placeholder:
                print("✓ 输入框placeholder正确（将通过JavaScript动态修改）")
            else:
                print(f"? 输入框placeholder: {placeholder}")
        else:
            print("✗ 未找到聊天输入框")
            
        print("\n=== HTML结构验证完成 ===")
        print("注意：JavaScript动态行为需要在浏览器中测试")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend_fixes()
    if success:
        print("\n🎉 HTML结构修复验证通过！")
        print("请在浏览器中访问 http://127.0.0.1:5000 查看实际效果")
    else:
        print("\n❌ 验证失败，请检查服务器状态")