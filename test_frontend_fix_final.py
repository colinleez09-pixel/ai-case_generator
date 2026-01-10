#!/usr/bin/env python3
"""
测试前端修复的最终版本
验证页面初始状态和对话逻辑是否正确
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_fixes():
    """测试前端修复"""
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # 访问页面
        driver.get("http://127.0.0.1:5000")
        
        print("✓ 页面加载成功")
        
        # 1. 检查初始状态：右侧对话框应该没有白色蒙皮
        overlay = driver.find_element(By.ID, "chatDisabledOverlay")
        overlay_classes = overlay.get_attribute("class")
        
        if "hidden" in overlay_classes:
            print("✓ 初始状态：对话框遮罩已隐藏")
        else:
            print("✗ 初始状态：对话框遮罩仍然显示")
            
        # 2. 检查初始消息是否显示
        chat_messages = driver.find_element(By.ID, "chatMessages")
        messages = chat_messages.find_elements(By.CLASS_NAME, "message")
        
        if len(messages) > 0:
            first_message = messages[0].find_element(By.CLASS_NAME, "message-content").text
            if "请先在左侧上传" in first_message:
                print("✓ 初始消息显示正确")
            else:
                print(f"✗ 初始消息内容不正确: {first_message}")
        else:
            print("✗ 没有找到初始消息")
            
        # 3. 检查输入框和发送按钮状态
        chat_input = driver.find_element(By.ID, "chatInput")
        send_btn = driver.find_element(By.ID, "sendBtn")
        
        if chat_input.get_attribute("disabled") == "true":
            print("✓ 聊天输入框正确禁用")
        else:
            print("✗ 聊天输入框应该被禁用")
            
        if send_btn.get_attribute("disabled") == "true":
            print("✓ 发送按钮正确禁用")
        else:
            print("✗ 发送按钮应该被禁用")
            
        # 4. 检查placeholder文本
        placeholder = chat_input.get_attribute("placeholder")
        if "请先上传文件并点击开始生成" in placeholder:
            print("✓ 输入框placeholder文本正确")
        else:
            print(f"✗ 输入框placeholder文本不正确: {placeholder}")
            
        print("\n=== 前端修复测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("开始测试前端修复...")
    test_frontend_fixes()