#!/usr/bin/env python3
"""
直接测试JavaScript文件是否有语法错误
"""

import requests
import re

def test_javascript_syntax():
    """测试JavaScript语法"""
    
    try:
        # 获取JavaScript文件
        response = requests.get("http://127.0.0.1:5000/static/script.js", timeout=10)
        response.raise_for_status()
        
        js_content = response.text
        print(f"JavaScript文件大小: {len(js_content)} 字符")
        
        # 检查第40行附近的内容
        lines = js_content.split('\n')
        if len(lines) >= 40:
            print(f"第40行: {lines[39]}")
            print(f"第41行: {lines[40] if len(lines) > 40 else 'N/A'}")
            print(f"第42行: {lines[41] if len(lines) > 41 else 'N/A'}")
        
        # 检查是否有明显的语法错误
        syntax_issues = []
        
        # 检查未闭合的字符串
        in_string = False
        string_char = None
        for i, line in enumerate(lines, 1):
            for j, char in enumerate(line):
                if char in ['"', "'"] and (j == 0 or line[j-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
            
            # 如果行结束时仍在字符串中，可能有问题
            if in_string and not line.strip().endswith('\\'):
                syntax_issues.append(f"第{i}行可能有未闭合的字符串: {line.strip()}")
        
        if syntax_issues:
            print("发现可能的语法问题:")
            for issue in syntax_issues:
                print(f"  - {issue}")
        else:
            print("✓ 未发现明显的语法错误")
            
        return len(syntax_issues) == 0
        
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求JavaScript文件失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试JavaScript语法...")
    success = test_javascript_syntax()
    if success:
        print("\n🎉 JavaScript语法检查通过！")
    else:
        print("\n❌ JavaScript语法检查失败")