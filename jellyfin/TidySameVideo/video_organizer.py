#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频文件整理工具 - TidySameVideo

本工具可以扫描目录中的视频文件，识别相似文件组，并智能地整理它们。
主要功能：
- 扫描多个目录中的视频文件
- 智能识别相似文件名的文件组
- 生成整理任务并验证
- 并行执行文件移动/复制操作
- 生成详细的执行报告

使用方式请参考帮助文档或运行 `python -m video_organizer --help`
"""

import os
import sys
from typing import List, Dict, Any, Optional

# 导入子模块
from utils import setup_logging, load_from_json, save_to_json, export_report
from data_processor import scan_multiple_directories, find_similar_file_groups, create_inverted_index
from task_generator import generate_move_tasks, validate_move_tasks, generate_execution_summary
from parallel_executor import parallel_execute_tasks
from cli import main as cli_main

def main(directories: Optional[List[str]] = None, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    主函数接口，提供向后兼容的功能入口
    
    参数:
        directories: 要扫描的目录列表
        output_dir: 整理后的输出目录
    
    返回:
        执行结果字典
    """
    # 配置日志
    setup_logging()
    
    # 如果没有提供参数，使用当前目录
    if directories is None:
        directories = [os.getcwd()]
    
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "organized")
    
    print("\n=== TidySameVideo - 视频文件整理工具 ===\n")
    print("步骤1: 扫描目录...")
    # 扫描目录
    file_list = scan_multiple_directories(directories)
    if not file_list:
        print("未发现任何文件，程序退出")
        return {"error": "未发现文件"}
    
    print(f"✓ 扫描完成，发现 {len(file_list)} 个文件")
    
    print("步骤2: 创建索引并查找相似文件...")
    # 创建倒排索引
    inverted_index = create_inverted_index(file_list)
    
    # 查找相似文件组
    similar_groups = find_similar_file_groups(file_list, inverted_index)
    if not similar_groups:
        print("✓ 未发现相似文件组，无需整理")
        return {"status": "no_groups", "file_count": len(file_list)}
    
    print(f"✓ 发现 {len(similar_groups)} 组相似文件")
    
    print("步骤3: 生成移动任务...")
    # 生成移动任务
    tasks, conflicts = generate_move_tasks(similar_groups, output_dir)
    
    print("步骤4: 验证任务...")
    # 验证任务
    valid_tasks, invalid_tasks = validate_move_tasks(tasks)
    
    print("步骤5: 生成执行摘要...")
    # 生成执行摘要
    summary = generate_execution_summary(valid_tasks, conflicts, invalid_tasks)
    
    # 保存结果
    results_file = "organization_results.json"
    result_data = {
        "tasks": valid_tasks,
        "conflicts": conflicts,
        "invalid_tasks": invalid_tasks,
        "summary": summary
    }
    save_to_json(result_data, results_file)
    
    print("\n=== 执行计划摘要 ===")
    print(f"总计任务数: {summary['total_tasks']}")
    print(f"冲突数: {summary['conflicts']}")
    print(f"无效任务数: {summary['invalid_tasks']}")
    print(f"估计数据量: {summary['estimated_size_mb']:.2f} MB")
    
    # 提示用户如何执行任务
    if valid_tasks:
        print("\n执行命令示例:")
        print(f"  python -m video_organizer --execute-tasks {results_file}")
    
    return {
        "status": "ready",
        "total_files": len(file_list),
        "similar_groups": len(similar_groups),
        "tasks": len(valid_tasks),
        "results_file": results_file
    }

def cli_main_wrapper():
    """命令行入口函数包装器"""
    # 调用cli模块中的main函数
    sys.exit(cli_main())

# 保持向后兼容性
if __name__ == "__main__":
    # 如果是直接运行脚本，调用CLI主函数
    cli_main_wrapper()