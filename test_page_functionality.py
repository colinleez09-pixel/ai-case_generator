#!/usr/bin/env python3
"""
测试页面功能是否正常
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def test_page_functionality():
    """测试页面功能"""
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        print("正在访问页面...")
        driver.get("http://127.0.0.1:5000")
        
        # 等待页面加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("✓ 页面加载成功")
        
        # 检查JavaScript是否有错误
        js_errors = driver.get_log('browser')
        # 过滤掉非关键错误（如favicon.ico 404错误）
        critical_js_errors = []
        for log in js_errors:
            if log['level'] == 'SEVERE':
                message = log['message']
                # 忽略favicon和GPU相关的错误
                if 'favicon.ico' not in message and 'SharedImageManager' not in message:
                    critical_js_errors.append(log)
        
        if critical_js_errors:
            print("✗ 发现关键JavaScript错误:")
            for error in critical_js_errors:
                print(f"  - {error['message']}")
            return False
        else:
            print("✓ 没有关键JavaScript错误")
        
        # 检查关键元素是否存在
        elements_to_check = [
            ("chatMessages", "聊天消息容器"),
            ("chatInput", "聊天输入框"),
            ("sendBtn", "发送按钮"),
            ("generateBtn", "生成按钮"),
            ("caseFileInput", "文件上传输入"),
        ]
        
        for element_id, description in elements_to_check:
            try:
                element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                print(f"✓ 找到{description}")
            except TimeoutException:
                print(f"✗ 未找到{description} (ID: {element_id})")
                return False
        
        # 检查初始消息是否显示
        try:
            chat_messages = driver.find_element(By.ID, "chatMessages")
            messages = chat_messages.find_elements(By.CLASS_NAME, "message")
            
            if len(messages) > 0:
                first_message_text = messages[0].text
                if "AI 测试用例生成助手" in first_message_text:
                    print("✓ 初始消息正确显示")
                else:
                    print(f"✗ 初始消息内容不正确: {first_message_text}")
                    return False
            else:
                print("✗ 没有找到初始消息")
                return False
                
        except Exception as e:
            print(f"✗ 检查初始消息时出错: {e}")
            return False
        
        # 检查输入框状态
        try:
            chat_input = driver.find_element(By.ID, "chatInput")
            send_btn = driver.find_element(By.ID, "sendBtn")
            
            if chat_input.get_attribute("disabled") == "true":
                print("✓ 聊天输入框正确禁用")
            else:
                print("✗ 聊天输入框应该被禁用")
                return False
                
            if send_btn.get_attribute("disabled") == "true":
                print("✓ 发送按钮正确禁用")
            else:
                print("✗ 发送按钮应该被禁用")
                return False
                
        except Exception as e:
            print(f"✗ 检查输入框状态时出错: {e}")
            return False
        
        # 检查遮罩层状态
        try:
            overlay = driver.find_element(By.ID, "chatDisabledOverlay")
            overlay_classes = overlay.get_attribute("class")
            
            if "hidden" in overlay_classes:
                print("✓ 遮罩层正确隐藏")
            else:
                print("✗ 遮罩层应该被隐藏")
                return False
                
        except Exception as e:
            print(f"✗ 检查遮罩层状态时出错: {e}")
            return False
        
        print("\n=== 页面功能测试完成 ===")
        return True
        
    except WebDriverException as e:
        print(f"✗ WebDriver错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("开始测试页面功能...")
    success = test_page_functionality()
    if success:
        print("\n🎉 页面功能测试通过！")
        print("页面已正常工作，JavaScript无错误，所有功能正常")
    else:
        print("\n❌ 页面功能测试失败")
        print("请检查浏览器控制台获取更多错误信息")