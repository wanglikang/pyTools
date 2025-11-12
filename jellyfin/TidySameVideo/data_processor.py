import os
import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from utils import clean_filename
import json
import tempfile

def scan_directory(directory: str, extensions: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """扫描目录中的文件，返回文件信息列表"""
    if not os.path.isdir(directory):
        logging.error(f"目录不存在: {directory}")
        return []
    
    if extensions is None:
        # 默认视频文件扩展名
        extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    file_list = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                _, ext = os.path.splitext(file.lower())
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_info = {
                            'path': file_path,
                            'name': file,
                            'size': file_size,
                            'directory': root
                        }
                        file_list.append(file_info)
                    except Exception as e:
                        logging.warning(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
        
        logging.info(f"扫描目录完成: {directory}, 发现{len(file_list)}个文件")
    except Exception as e:
        logging.error(f"扫描目录失败: {directory}, 错误: {str(e)}")
    
    return file_list

def scan_multiple_directories(directories: List[str], extensions: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """扫描多个目录，合并结果"""
    all_files = []
    for directory in directories:
        files = scan_directory(directory, extensions)
        all_files.extend(files)
    
    logging.info(f"扫描所有目录完成，总计发现{len(all_files)}个文件")
    return all_files

def create_inverted_index(file_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """创建文件名倒排索引，用于快速查找相似文件，并将索引保存到临时文件便于复查"""
    
    index = {}
    
    for file_info in file_list:
        # 获取文件名（不含扩展名）
        base_name = os.path.splitext(file_info['name'])[0]
        cleaned_name = clean_filename(base_name)
        
        # 提取关键字（移除常见的数字标识等）
        # 移除非字母数字字符，保留中文
        keywords = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', cleaned_name)
        
        # 添加到索引
        for keyword in keywords:
            if len(keyword) > 1:  # 忽略单字符关键词
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(file_info)
    
    # 将倒排索引保存到临时文件，便于人工复查
    try:
        # 使用当前目录作为保存位置，不再依赖外部output参数
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
            # 将文件路径转换为字符串以便序列化
            serializable_index = {}
            for keyword, file_infos in index.items():
                serializable_index[keyword] = [
                    {k: str(v) if k == 'path' else v for k, v in fi.items()} for fi in file_infos
                ]
            json.dump(serializable_index, tmp_file, ensure_ascii=False, indent=2)
            logging.info(f"倒排索引已保存到临时文件: {tmp_file.name}")
    except Exception as e:
        logging.warning(f"保存倒排索引到临时文件失败: {e}")
    
    logging.info(f"倒排索引创建完成，包含{len(index)}个关键词")
    return index

def are_files_similar(file1: Dict[str, Any], file2: Dict[str, Any], 
                      min_similarity_ratio: float = 0.6, size_threshold_mb: float = 10) -> bool:
    """判断两个文件是否相似"""
    # 获取文件名（不含扩展名）
    name1 = os.path.splitext(file1['name'])[0]
    name2 = os.path.splitext(file2['name'])[0]
    
    # 清理文件名
    clean1 = clean_filename(name1)
    clean2 = clean_filename(name2)
    
    # 如果文件名几乎相同，直接返回True
    if abs(len(clean1) - len(clean2)) < 5 and clean1 in clean2 or clean2 in clean1:
        return True
    
    # 计算文件名的Jaccard相似度
    set1 = set(clean1)
    set2 = set(clean2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return False
    
    similarity_ratio = intersection / union
    
    # 对于大文件，放宽相似度要求
    avg_size_mb = (file1['size'] + file2['size']) / 2 / (1024 * 1024)
    if avg_size_mb > size_threshold_mb:
        min_similarity_ratio = max(0.4, min_similarity_ratio - 0.1)
    
    return similarity_ratio >= min_similarity_ratio

def find_similar_file_groups(file_list: List[Dict[str, Any]], 
                             inverted_index: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[List[Dict[str, Any]]]:
    """查找相似文件组"""
    if not file_list:
        return []
    
    # 如果没有提供索引，创建一个
    if inverted_index is None:
        inverted_index = create_inverted_index(file_list)
    
    # 标记已处理的文件
    processed = set()
    similar_groups = []
    
    for i, file1 in enumerate(file_list):
        if i in processed:
            continue
        
        group = [file1]
        processed.add(i)
        
        # 获取与当前文件可能相似的候选文件
        base_name = os.path.splitext(file1['name'])[0]
        cleaned_name = clean_filename(base_name)
        keywords = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', cleaned_name)
        
        # 收集候选文件
        candidates = set()
        for keyword in keywords:
            if keyword in inverted_index:
                for candidate in inverted_index[keyword]:
                    # 找到候选文件在file_list中的索引
                    for j, f in enumerate(file_list):
                        if f['path'] == candidate['path'] and j not in processed:
                            candidates.add(j)
                            break
        
        # 检查候选文件是否相似 - 创建副本以避免在迭代过程中修改集合
        candidates_list = list(candidates)
        for j in candidates_list:
            if j not in processed:
                file2 = file_list[j]
                if are_files_similar(file1, file2):
                    group.append(file2)
                    processed.add(j)
                    
                    # 递归查找与新加入文件相似的文件
                    j_candidates = set()
                    j_base_name = os.path.splitext(file2['name'])[0]
                    j_cleaned_name = clean_filename(j_base_name)
                    j_keywords = re.findall(r'[一-龥]+|[a-zA-Z]+', j_cleaned_name)
                    
                    for j_keyword in j_keywords:
                        if j_keyword in inverted_index:
                            for j_candidate in inverted_index[j_keyword]:
                                for k, f in enumerate(file_list):
                                    if f['path'] == j_candidate['path'] and k not in processed:
                                        j_candidates.add(k)
                                        break
                    
                    # 将新的候选添加到集合中，并同时添加到遍历列表中
                    for new_j in j_candidates:
                        if new_j not in processed and new_j not in candidates_list:
                            candidates_list.append(new_j)
                    candidates.update(j_candidates)
        
        # 只添加包含多个文件的组
        if len(group) > 1:
            # 按大小降序排序，优先保留大文件
            group.sort(key=lambda x: x['size'], reverse=True)
            similar_groups.append(group)
    
    logging.info(f"找到{len(similar_groups)}组相似文件")
    return similar_groups