import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from utils import generate_folder_name, check_path_length, sanitize_folder_name
from data_processor import find_similar_file_groups

def detect_conflicts(task: Dict[str, Any], existing_tasks: List[Dict[str, Any]], context = None) -> Optional[Dict[str, str]]:
    """检测任务冲突"""
    target_path = task['target']
    
    # 检查目标文件是否已存在
    if os.path.exists(target_path):
        existing_size = os.path.getsize(target_path)
        new_size = task['size']
        
        if existing_size == new_size:
            return {
                'source': task['source'],
                'target': target_path,
                'type': 'file_exists_same_size'
            }
        else:
            return {
                'source': task['source'],
                'target': target_path,
                'type': 'file_exists_different_size'
            }
    
    # 检查与其他任务的目标是否冲突
    for existing_task in existing_tasks:
        if existing_task['target'] == target_path:
            return {
                'source': task['source'],
                'target': target_path,
                'type': 'task_conflict'
            }
    
    # 检查路径长度
    if not check_path_length(target_path):
        return {
            'source': task['source'],
            'target': target_path,
            'type': 'path_too_long'
        }
    
    return None

def generate_move_tasks(similar_groups: List[List[Dict[str, Any]]], 
                       output_dir: str, 
                       strategy: str = "keep_best",
                       context = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """生成移动任务和冲突列表"""
    if not similar_groups:
        logging.info("没有找到相似文件组，不需要生成移动任务")
        return [], []
    
    tasks = []
    conflicts = []
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    for group_idx, file_group in enumerate(similar_groups):
        # 生成文件夹名称
        folder_name = generate_folder_name(file_group)
        group_folder = os.path.join(output_dir, folder_name)
        
        # 处理文件夹名称冲突
        counter = 1
        original_folder = group_folder
        while os.path.exists(group_folder) and len(os.listdir(group_folder)) > 0:
            group_folder = f"{original_folder}_{counter}"
            counter += 1
        
        # 根据策略处理文件
        if strategy == "keep_best":
            # 保留最大的文件，移动其他文件
            best_file = file_group[0]  # 已经按大小排序，第一个是最大的
            
            # 创建任务
            for i, file_info in enumerate(file_group):
                if i == 0:  # 最大的文件保持不变
                    continue
                
                # 生成目标文件名
                file_name = os.path.basename(file_info['path'])
                target_path = os.path.join(group_folder, file_name)
                
                task = {
                    'source': file_info['path'],
                    'target': target_path,
                    'size': file_info['size'],
                    'group_index': group_idx,
                    'file_index': i
                }
                
                # 检测冲突
                conflict = detect_conflicts(task, tasks, context)
                if conflict:
                    conflicts.append(conflict)
                else:
                    tasks.append(task)
        
        elif strategy == "move_all":
            # 移动所有文件
            for i, file_info in enumerate(file_group):
                file_name = os.path.basename(file_info['path'])
                target_path = os.path.join(group_folder, file_name)
                
                task = {
                    'source': file_info['path'],
                    'target': target_path,
                    'size': file_info['size'],
                    'group_index': group_idx,
                    'file_index': i
                }
                
                # 检测冲突
                conflict = detect_conflicts(task, tasks, context)
                if conflict:
                    conflicts.append(conflict)
                else:
                    tasks.append(task)
    
    logging.info(f"生成了{len(tasks)}个移动任务，发现{len(conflicts)}个冲突")
    return tasks, conflicts

def validate_move_tasks(tasks: List[Dict[str, Any]], context = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """验证移动任务的有效性"""
    valid_tasks = []
    invalid_tasks = []
    
    for task in tasks:
        source = task['source']
        target = task['target']
        
        # 检查源文件是否存在
        if not os.path.exists(source):
            invalid_tasks.append({
                'source': source,
                'target': target,
                'reason': '源文件不存在'
            })
            continue
        
        # 检查源文件是否为文件
        if not os.path.isfile(source):
            invalid_tasks.append({
                'source': source,
                'target': target,
                'reason': '源路径不是文件'
            })
            continue
        
        # 检查目标目录是否可写
        target_dir = os.path.dirname(target)
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                invalid_tasks.append({
                    'source': source,
                    'target': target,
                    'reason': f'无法创建目标目录: {str(e)}'
                })
                continue
        
        # 检查路径长度
        if not check_path_length(source) or not check_path_length(target):
            invalid_tasks.append({
                'source': source,
                'target': target,
                'reason': '路径长度超过系统限制'
            })
            continue
        
        valid_tasks.append(task)
    
    logging.info(f"验证完成，{len(valid_tasks)}个有效任务，{len(invalid_tasks)}个无效任务")
    return valid_tasks, invalid_tasks

def generate_execution_summary(tasks: List[Dict[str, Any]], 
                               conflicts: List[Dict[str, str]],
                               invalid_tasks: List[Dict[str, str]],
                               context = None) -> Dict[str, Any]:
    """生成执行计划摘要"""
    summary = {
        'total_tasks': len(tasks),
        'conflicts': len(conflicts),
        'invalid_tasks': len(invalid_tasks),
        'estimated_size_mb': sum(task['size'] for task in tasks) / (1024 * 1024),
        'task_details': []
    }
    
    # 添加部分任务详情作为预览
    for i, task in enumerate(tasks[:10]):  # 只显示前10个任务
        summary['task_details'].append({
            'source': task['source'],
            'target': task['target'],
            'size_mb': task['size'] / (1024 * 1024)
        })
    
    if len(tasks) > 10:
        summary['task_details'].append({'note': f'... 还有{len(tasks) - 10}个任务未显示'})
    
    return summary