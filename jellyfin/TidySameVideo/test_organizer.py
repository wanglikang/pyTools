#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证重构后的视频文件整理工具功能

此脚本用于测试重构后的各个模块是否正常工作，包括：
- 工具函数测试
- 数据处理测试
- 任务生成测试
- 并行执行测试
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加当前目录到Python路径，确保可以导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入需要测试的模块
from utils import setup_logging, clean_filename, save_to_json, load_from_json
from data_processor import scan_directory, create_inverted_index, are_files_similar
from task_generator import generate_move_tasks, validate_move_tasks, generate_execution_summary
from parallel_executor import calculate_optimal_workers, execute_move_task
from video_organizer import main as organizer_main

def test_utils():
    """测试工具函数"""
    print("\n=== 测试工具函数 ===")
    
    # 测试日志设置
    setup_logging()
    print("✓ 日志设置成功")
    
    # 测试文件名清理
    test_filenames = [
        "Sample.Movie.2023.1080p.BluRay.x264",
        "Another.Movie.(2022)[1080p][WebRip]",
        "Series.S01E05.720p.HDTV.x265"
    ]
    
    print("文件名清理测试:")
    for fname in test_filenames:
        cleaned = clean_filename(fname)
        print(f"  '{fname}' -> '{cleaned}'")
    
    # 测试JSON操作
    test_data = {"test": "data", "numbers": [1, 2, 3]}
    temp_file = tempfile.mktemp(suffix=".json")
    try:
        save_to_json(test_data, temp_file)
        loaded_data = load_from_json(temp_file)
        assert loaded_data == test_data, "JSON保存加载数据不匹配"
        print("✓ JSON操作测试成功")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def create_test_files(test_dir):
    """创建测试文件结构"""
    # 创建文件列表，分别标记为视频文件和非视频文件
    all_files = [
        "movie1_720p.mp4",    # 视频
        "movie1_1080p.mkv",   # 视频
        "movie1.srt",        # 字幕
        "movie2_2023.mp4",    # 视频
        "movie2.sub",        # 字幕
        "series_s01e01.mp4",  # 视频
        "series_s01e02.mkv",  # 视频
        "series_s01e01.nfo"   # 元数据
    ]
    
    # 视频文件扩展名
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    for fname in all_files:
        file_path = os.path.join(test_dir, fname)
        with open(file_path, 'w') as f:
            # 写入一些内容，使其成为有效文件
            f.write(f"This is a test file: {fname}")
    
    # 计算预期的视频文件数量
    video_files_count = sum(1 for f in all_files if os.path.splitext(f)[1] in video_extensions)
    
    return all_files, video_files_count

def test_data_processor():
    """测试数据处理模块"""
    print("\n=== 测试数据处理模块 ===")
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as test_dir:
        print(f"创建测试目录: {test_dir}")
        all_files, expected_video_count = create_test_files(test_dir)
        
        # 测试目录扫描
        print("测试目录扫描:")
        files = scan_directory(test_dir)
        print(f"  发现 {len(files)} 个视频文件")
        assert len(files) == expected_video_count, f"扫描文件数量不匹配: {len(files)} != {expected_video_count}"
        
        # 测试倒排索引
        print("测试倒排索引:")
        index = create_inverted_index(files)
        print(f"  创建了 {len(index)} 个索引项")
        
        # 测试相似度比较 - 修改为使用正确的文件字典格式
        print("测试相似度比较:")
        # 创建测试用的文件字典，包含所需的所有字段
        file_dict1 = {'name': 'movie1_720p.mp4', 'path': os.path.join(test_dir, 'movie1_720p.mp4'), 'size': 100 * 1024 * 1024}  # 100MB
        file_dict2 = {'name': 'movie1_1080p.mkv', 'path': os.path.join(test_dir, 'movie1_1080p.mkv'), 'size': 200 * 1024 * 1024}  # 200MB
        file_dict3 = {'name': 'movie2_2023.mp4', 'path': os.path.join(test_dir, 'movie2_2023.mp4'), 'size': 150 * 1024 * 1024}  # 150MB
        
        # 进行相似度测试
        test_cases = [
            (file_dict1, file_dict2, True),  # 相同电影的不同版本应该相似
            (file_dict1, file_dict3, False), # 不同电影应该不相似
        ]
        
        for i, (f1, f2, expected) in enumerate(test_cases):
            result = are_files_similar(f1, f2)
            status = "✓" if result == expected else "✗"
            print(f"  {status} 测试 #{i+1}: '{f1['name']}' 和 '{f2['name']}' {'相似' if result else '不相似'} (期望: {expected})")
            
        print("✓ 数据处理模块测试完成")

def test_task_generator():
    """测试任务生成模块"""
    print("\n=== 测试任务生成模块 ===")
    
    with tempfile.TemporaryDirectory() as test_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # 创建测试文件
            all_files, _ = create_test_files(test_dir)
            
            # 扫描文件
            files = scan_directory(test_dir)
            
            # 创建索引
            index = create_inverted_index(files)
            
            # 创建简单的文件组，只使用扫描到的视频文件
            groups = []
            if len(files) >= 2:
                groups.append([files[0], files[1]])  # 第一个和第二个视频文件一组
            if len(files) >= 3:
                groups.append([files[2]])  # 第三个视频文件单独一组
            
            # 测试任务生成
            print("测试任务生成:")
            tasks, conflicts = generate_move_tasks(groups, output_dir)
            print(f"  生成了 {len(tasks)} 个任务, {len(conflicts)} 个冲突")
            
            # 测试任务验证
            print("测试任务验证:")
            valid_tasks, invalid_tasks = validate_move_tasks(tasks)
            print(f"  有效任务: {len(valid_tasks)}, 无效任务: {len(invalid_tasks)}")
            
            # 测试执行摘要生成
            summary = generate_execution_summary(valid_tasks, conflicts, invalid_tasks)
            print(f"  执行摘要: 总任务={summary['total_tasks']}, 冲突={summary['conflicts']}")
            
            print("✓ 任务生成模块测试完成")

def test_main_function():
    """测试主函数功能"""
    print("\n=== 测试主函数功能 ===")
    
    with tempfile.TemporaryDirectory() as test_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # 创建测试文件
            create_test_files(test_dir)
            
            # 调用主函数进行测试
            print(f"调用主函数测试，目录: {test_dir}, 输出: {output_dir}")
            result = organizer_main([test_dir], output_dir)
            
            # 检查结果
            print(f"主函数执行结果: {result.get('status')}")
            print(f"  总文件数: {result.get('total_files')}")
            print(f"  相似组数: {result.get('similar_groups')}")
            print(f"  生成任务: {result.get('tasks')}")
            
            # 检查结果文件
            results_file = os.path.join(os.getcwd(), "organization_results.json")
            if os.path.exists(results_file):
                print(f"✓ 结果文件已生成: {results_file}")
            
            print("✓ 主函数测试完成")

def run_all_tests():
    """运行所有测试"""
    print("=== 开始测试重构后的代码 ===")
    
    try:
        # 运行各个测试模块
        test_utils()
        test_data_processor()
        test_task_generator()
        test_main_function()
        
        print("\n=== 所有测试通过！ ===")
        return True
        
    except Exception as e:
        print(f"\n=== 测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)