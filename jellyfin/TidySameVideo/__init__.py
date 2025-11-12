#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TidySameVideo - 视频文件整理工具包

本包提供了一套完整的视频文件整理功能，包括：
- 文件扫描与索引
- 相似文件识别与分组
- 移动任务生成与验证
- 并行执行框架
- 命令行接口
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "TidySameVideo Team"
__description__ = "视频文件智能整理工具"

# 导出主要功能
from .video_organizer import main
from .utils import setup_logging
from .data_processor import scan_directory, scan_multiple_directories
from .task_generator import generate_move_tasks
from .parallel_executor import parallel_execute_tasks

__all__ = [
    'main',
    'setup_logging',
    'scan_directory',
    'scan_multiple_directories',
    'generate_move_tasks',
    'parallel_execute_tasks'
]