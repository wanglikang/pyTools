#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：验证分词功能是否正常工作
"""

import sys
import os
from context import VideoOrganizerContext
from data_processor import find_similar_file_groups

def test_text_segmentation():
    """测试文本分词功能"""
    print("=== 测试文本分词功能 ===")
    
    # 创建一个简单的上下文对象
    context = VideoOrganizerContext(
        scan_directories=[os.getcwd()],
        output_dir=os.getcwd()
    )
    
    # 测试中文分词
    print("\n测试中文分词:")
    test_texts = [
        "海贼王第1000集.mp4",
        "进击的巨人最终季.part1.mkv",
        "鬼灭之刃无限列车篇.mkv",
        "我的三体之章北海传.ep01.mp4"
    ]
    
    for text in test_texts:
        # 清理文件名（模拟clean_filename函数）
        cleaned = ''.join([c for c in text if c.isalnum() or c.isspace() or '\u4e00' <= c <= '\u9fff'])
        # 使用分词功能
        words = context._segment_text(cleaned)
        print(f"原始文本: {text}")
        print(f"分词结果: {words}")
        print()
    
    # 测试日文分词（如果mecab可用）
    print("测试日文分词:")
    jp_texts = [
        "鬼滅の刃第1話.mp4",
        "進撃の巨人最終話.mkv",
        "ワンピース新章開始.avi"
    ]
    
    for text in jp_texts:
        # 清理文件名
        cleaned = ''.join([c for c in text if c.isalnum() or c.isspace() or '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff'])
        # 使用分词功能
        words = context._segment_text(cleaned)
        print(f"原始文本: {text}")
        print(f"分词结果: {words}")
        print()

def test_inverted_index_creation():
    """测试倒排索引创建"""
    print("=== 测试倒排索引创建 ===")
    
    # 创建一个带有模拟文件列表的上下文对象
    context = VideoOrganizerContext(
        scan_directories=[os.getcwd()],
        output_dir=os.getcwd()
    )
    
    # 添加一些模拟文件
    mock_files = [
        {'path': os.path.join(os.getcwd(), '海贼王第1000集.mp4'), 'name': '海贼王第1000集.mp4', 'size': 1000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '海贼王剧场版.mp4'), 'name': '海贼王剧场版.mp4', 'size': 2000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '进击的巨人最终季.part1.mkv'), 'name': '进击的巨人最终季.part1.mkv', 'size': 3000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '进击的巨人最终季.part2.mkv'), 'name': '进击的巨人最终季.part2.mkv', 'size': 3500000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '鬼灭之刃无限列车篇.mkv'), 'name': '鬼灭之刃无限列车篇.mkv', 'size': 4000000, 'directory': os.getcwd()}
    ]
    
    context.update_file_list(mock_files)
    
    # 创建倒排索引
    inverted_index = context.create_inverted_index()
    
    # 打印部分索引内容以验证
    print(f"倒排索引包含 {len(inverted_index)} 个关键词")
    print("前5个关键词及其对应的文件数量:")
    
    count = 0
    for keyword, files in inverted_index.items():
        print(f"'{keyword}': {len(files)} 个文件")
        count += 1
        if count >= 5:
            break

def test_similar_file_detection():
    """测试相似文件检测功能"""
    print("=== 测试相似文件检测功能 ===")
    
    # 创建上下文对象并添加模拟文件
    context = VideoOrganizerContext(
        scan_directories=[os.getcwd()],
        output_dir=os.getcwd()
    )
    
    mock_files = [
        {'path': os.path.join(os.getcwd(), '海贼王第1000集.mp4'), 'name': '海贼王第1000集.mp4', 'size': 1000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '海贼王剧场版.mp4'), 'name': '海贼王剧场版.mp4', 'size': 2000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '进击的巨人最终季.part1.mkv'), 'name': '进击的巨人最终季.part1.mkv', 'size': 3000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '进击的巨人最终季.part2.mkv'), 'name': '进击的巨人最终季.part2.mkv', 'size': 3500000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '鬼灭之刃无限列车篇.mkv'), 'name': '鬼灭之刃无限列车篇.mkv', 'size': 4000000, 'directory': os.getcwd()},
        {'path': os.path.join(os.getcwd(), '鬼滅の刃第一話.mp4'), 'name': '鬼滅の刃第一話.mp4', 'size': 2500000, 'directory': os.getcwd()}
    ]
    
    context.update_file_list(mock_files)
    
    # 查找相似文件组
    similar_groups = find_similar_file_groups(context)
    
    print(f"找到 {len(similar_groups)} 组相似文件")
    for i, group in enumerate(similar_groups, 1):
        print(f"\n组 {i} ({len(group)} 个文件):")
        for file in group:
            print(f"  - {file['name']} ({file['size'] / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    print("开始测试分词功能和相关优化...\n")
    
    try:
        test_text_segmentation()
        test_inverted_index_creation()
        test_similar_file_detection()
        
        print("\n=== 测试完成 ===")
        print("所有测试项目已成功执行！")
    except Exception as e:
        print(f"\n=== 测试失败 ===")
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)