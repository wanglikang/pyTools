#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试空行过滤功能
"""

# 测试文件路径
test_file = 'test_file.txt'

print("原始文件内容：")
print("=" * 30)
with open(test_file, 'r', encoding='utf-8') as f:
    original_content = f.read()
    print(original_content)

print("\n\n过滤空行后的内容：")
print("=" * 30)
with open(test_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 过滤空行
non_empty_lines = [line.rstrip('\n') for line in lines if line.strip()]
filtered_content = '\n'.join(non_empty_lines)
print(filtered_content)

print("\n\n原始行数：", len(lines))
print("过滤后行数：", len(non_empty_lines))
