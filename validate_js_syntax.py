#!/usr/bin/env python3
"""
JavaScript语法验证工具
"""

import subprocess
import sys
import os

def validate_js_syntax(file_path):
    """验证JavaScript文件的语法"""
    try:
        # 使用Node.js来检查语法
        result = subprocess.run([
            'node', '-c', file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {file_path} 语法正确")
            return True
        else:
            print(f"❌ {file_path} 语法错误:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠️ Node.js未安装，尝试使用Python解析...")
        return validate_js_with_python(file_path)

def validate_js_with_python(file_path):
    """使用Python简单检查JavaScript语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的括号匹配检查
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        line_num = 1
        char_num = 1
        
        for i, char in enumerate(content):
            if char == '\n':
                line_num += 1
                char_num = 1
            else:
                char_num += 1
                
            if char in brackets:
                stack.append((char, line_num, char_num))
            elif char in brackets.values():
                if not stack:
                    print(f"❌ 第{line_num}行第{char_num}列: 多余的 '{char}'")
                    return False
                
                open_char, open_line, open_char_num = stack.pop()
                expected = brackets[open_char]
                
                if char != expected:
                    print(f"❌ 第{line_num}行第{char_num}列: 期望 '{expected}' 但找到 '{char}'")
                    print(f"   对应的开括号在第{open_line}行第{open_char_num}列")
                    return False
        
        if stack:
            open_char, open_line, open_char_num = stack[-1]
            expected = brackets[open_char]
            print(f"❌ 第{open_line}行第{open_char_num}列: 未闭合的 '{open_char}'，期望 '{expected}'")
            return False
        
        print(f"✅ {file_path} 括号匹配正确")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def find_syntax_errors_around_line(file_path, target_line):
    """在指定行附近查找语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = max(0, target_line - 10)
        end = min(len(lines), target_line + 10)
        
        print(f"\n🔍 检查第{target_line}行附近的代码:")
        print("=" * 60)
        
        for i in range(start, end):
            line_content = lines[i].rstrip()
            marker = ">>> " if i + 1 == target_line else "    "
            print(f"{marker}{i+1:4d}: {line_content}")
        
        print("=" * 60)
        
        # 检查常见的语法错误
        if target_line <= len(lines):
            line = lines[target_line - 1]
            
            # 检查未闭合的括号
            open_count = line.count('{') - line.count('}')
            if open_count > 0:
                print(f"⚠️ 第{target_line}行可能有未闭合的大括号")
            
            # 检查多余的括号
            if '}' in line and line.strip() == '}':
                print(f"⚠️ 第{target_line}行可能是多余的闭合括号")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    file_path = "static/script.js"
    target_line = 2404
    
    print("🧪 JavaScript语法验证工具")
    print(f"📁 检查文件: {file_path}")
    print(f"🎯 目标行: {target_line}")
    
    # 验证整体语法
    is_valid = validate_js_syntax(file_path)
    
    # 分析目标行附近
    find_syntax_errors_around_line(file_path, target_line)
    
    if not is_valid:
        sys.exit(1)