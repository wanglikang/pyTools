#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理模块 - 实现文件移动任务的并行执行
"""

import os
import shutil
import logging
import concurrent.futures
import multiprocessing
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from utils import setup_logging, backup_file

# 尝试导入tqdm以支持进度显示
try:
    from tqdm import tqdm
except ImportError:
    # 如果没有安装tqdm，定义一个简单的替代函数
    def tqdm(iterable, **kwargs):
        return iterable

def calculate_optimal_workers(context = None) -> int:
    """计算最佳工作线程数
    
    Args:
        context: 上下文对象（可选）
    """
    # 获取CPU核心数
    cpu_count = multiprocessing.cpu_count()
    
    # 对于I/O密集型任务，可以使用比CPU核心数更多的线程
    # 但不要超过32个，以免系统资源过度消耗
    optimal_workers = min(cpu_count * 4, 32)
    
    logging.info(f"计算最佳工作线程数: CPU核心数={cpu_count}, 工作线程数={optimal_workers}")
    return optimal_workers

def execute_move_task(task: Dict[str, Any], context = None) -> Tuple[bool, str, Optional[str]]:
    """
    执行单个移动任务
    返回: (成功标志, 源文件路径, 错误信息(如果失败))
    
    Args:
        task: 任务信息字典
        context: 上下文对象（可选）
    """
    source = task['source']
    target = task['target']
    
    try:
        # 检查源文件是否存在
        if not os.path.exists(source):
            return False, source, f"源文件不存在: {source}"
        
        # 确保目标目录存在
        target_dir = os.path.dirname(target)
        os.makedirs(target_dir, exist_ok=True)
        
        # 检查目标文件是否已存在
        if os.path.exists(target):
            # 比较文件大小
            source_size = os.path.getsize(source)
            target_size = os.path.getsize(target)
            
            if source_size == target_size:
                logging.warning(f"目标文件已存在且大小相同，跳过: {target}")
                return True, source, None
            
            # 如果目标文件存在但大小不同，备份目标文件
            backup_path = backup_file(target)
            logging.warning(f"目标文件已存在且大小不同，已备份至: {backup_path}")
        
        # 执行文件复制
        shutil.copy2(source, target)
        logging.info(f"成功复制文件: {source} -> {target}")
        
        # 如果任务要求删除源文件
        if task.get('delete_source', False):
            try:
                os.remove(source)
                logging.info(f"成功删除源文件: {source}")
            except Exception as e:
                logging.error(f"删除源文件失败: {source}, 错误: {str(e)}")
        
        return True, source, None
        
    except Exception as e:
        logging.error(f"执行移动任务失败: {source} -> {target}, 错误: {str(e)}")
        return False, source, str(e)

def parallel_execute_tasks(tasks: List[Dict[str, Any]], max_workers: Optional[int] = None, context = None) -> Dict[str, Any]:
    """
    并行执行任务列表
    
    Args:
        tasks: 任务列表，每个任务包含source和target字段
        max_workers: 最大工作线程数，如果为None则自动计算
        context: 上下文对象（可选）
    
    Returns:
        包含执行结果的字典
    """
    if max_workers is None:
        max_workers = calculate_optimal_workers()
    
    logging.info(f"开始并行执行任务，任务总数: {len(tasks)}, 工作线程数: {max_workers}")
    
    results = {
        'total_tasks': len(tasks),
        'completed_tasks': 0,
        'failed_tasks': 0,
        'failed_files': [],
        'execution_time': 0
    }
    
    # 记录开始时间
    import time
    start_time = time.time()
    
    # 使用线程池并行执行任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {executor.submit(execute_move_task, task): task for task in tasks}
        
        # 使用tqdm显示进度
        with tqdm(total=len(tasks), desc="执行任务进度") as pbar:
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success, source, error_msg = future.result()
                    if success:
                        results['completed_tasks'] += 1
                    else:
                        results['failed_tasks'] += 1
                        results['failed_files'].append({
                            'source': source,
                            'target': task['target'],
                            'error': error_msg
                        })
                except Exception as e:
                    results['failed_tasks'] += 1
                    results['failed_files'].append({
                        'source': task['source'],
                        'target': task['target'],
                        'error': f"执行异常: {str(e)}"
                    })
                finally:
                    pbar.update(1)
    
    # 计算执行时间
    results['execution_time'] = time.time() - start_time
    
    logging.info(f"并行执行完成: 成功={results['completed_tasks']}, 失败={results['failed_tasks']}, "
                 f"用时={results['execution_time']:.2f}秒")
    
    return results