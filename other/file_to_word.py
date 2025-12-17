#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定文件夹下符合特定后缀的文件内容写入到Word文档中
支持递归遍历文件夹
"""

import os
import argparse
from docx import Document
from docx.shared import Inches

def file_to_word(folder_path, file_extensions, output_file):
    """
    将指定文件夹下符合特定后缀的文件内容写入到Word文档中
    
    Args:
        folder_path (str): 要遍历的文件夹路径
        file_extensions (list): 要匹配的文件后缀列表，如['.txt', '.py']
        output_file (str): 输出的Word文档路径
    """
    # 创建Word文档
    doc = Document()
    doc.add_heading('文件内容汇总', 0)
    
    # 递归遍历文件夹
    file_count = 0
    line_count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 检查文件后缀
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                file_count += 1
                
                try:
                    # 添加文件信息
                    relative_path = os.path.relpath(file_path, folder_path)
                    # doc.add_heading(f'文件 {file_count}: {relative_path}', level=1)
                    
                    # 读取文件内容并过滤空行
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 过滤空行
                    non_empty_lines = [line.rstrip('\n') for line in lines if line.strip()]
                    line_count += len(non_empty_lines)
                    content = '\n'.join(non_empty_lines)
                    
                    # 添加文件内容
                    doc.add_heading('内容:', level=2)
                    doc.add_paragraph(content)
                    
                    # 添加分页符
                    doc.add_page_break()
                    
                    print(f'已处理文件: {relative_path}')
                except Exception as e:
                    doc.add_heading('内容读取失败:', level=2)
                    doc.add_paragraph(f'错误信息: {str(e)}')
                    doc.add_page_break()
                    print(f'处理文件失败: {relative_path}, 错误: {str(e)}')
    
    # 保存文档
    doc.save(output_file)
    print(f'\n处理完成！共处理 {file_count} 个文件')
    print(f'共处理 {line_count} 行内容')
    print(f'输出文件: {output_file}')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将指定文件夹下符合特定后缀的文件内容写入到Word文档中')
    parser.add_argument('-f', '--folder', required=True, help='要遍历的文件夹路径')
    parser.add_argument('-e', '--extensions', required=True, help='要匹配的文件后缀，多个后缀用逗号分隔，如：.txt,.py,.md')
    parser.add_argument('-o', '--output', default='file_content.docx', help='输出的Word文档路径，默认：file_content.docx')
    
    args = parser.parse_args()
    
    # 处理文件后缀参数
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    # 验证文件夹路径
    if not os.path.exists(args.folder):
        print(f'错误：文件夹路径不存在：{args.folder}')
        return
    
    # 执行转换
    file_to_word(args.folder, extensions, args.output)

if __name__ == '__main__':
    main()