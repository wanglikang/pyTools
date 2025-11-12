import os
import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from utils import clean_filename
from context import VideoOrganizerContext
from keyword_filter import get_keyword_blacklist, is_blacklisted_keyword

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

def scan_multiple_directories(context: VideoOrganizerContext, extensions: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """扫描多个目录，合并结果
    
    Args:
        context: 包含扫描目录信息的上下文对象
        extensions: 文件扩展名集合
        
    Returns:
        List[Dict[str, Any]]: 文件信息列表
    """
    all_files = []
    for directory in context.scan_directories:
        files = scan_directory(directory, extensions)
        all_files.extend(files)
    
    # 更新上下文
    context.update_file_list(all_files)
    
    logging.info(f"扫描所有目录完成，总计发现{len(all_files)}个文件")
    return all_files

# 黑名单功能已移至keyword_filter模块

def create_inverted_index(context: VideoOrganizerContext) -> Dict[str, List[Dict[str, Any]]]:
    """创建文件名倒排索引，用于快速查找相似文件，并将索引保存到临时文件便于复查
    
    Args:
        context: 包含文件列表和输出路径的上下文对象
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: 倒排索引
    """
    # 确保黑名单已加载
    get_keyword_blacklist()
    return context.create_inverted_index()

def are_files_similar(file1: Dict[str, Any], file2: Dict[str, Any], context: Optional[VideoOrganizerContext] = None, min_similarity_ratio: float = 0.55, size_threshold_mb: float = 500.0) -> bool:
    """判断两个文件是否相似
    
    Args:
        file1: 第一个文件的信息
        file2: 第二个文件的信息
        context: 上下文对象，用于访问分词功能
        min_similarity_ratio: 最小相似度阈值
        size_threshold_mb: 文件大小阈值，大于此值的文件会放宽相似度要求
        
    Returns:
        bool: 文件是否相似
    """
    # 如果两个文件在同一个目录，认为它们不是重复的
    if file1['directory'] == file2['directory']:
        return False
    
    # 提取文件名（不包含扩展名）
    name1 = os.path.splitext(file1['name'])[0]
    name2 = os.path.splitext(file2['name'])[0]
    
    # 清理文件名
    clean1 = clean_filename(name1)
    clean2 = clean_filename(name2)
    
    # 如果文件名几乎相同，直接返回True
    if abs(len(clean1) - len(clean2)) < 5 and (clean1 in clean2 or clean2 in clean1):
        return True
    
    # 使用关键字相似度计算（如果提供了上下文）
    if context:
        # 分词处理两个文件名
        keywords1 = context._segment_text(clean1)
        keywords2 = context._segment_text(clean2)
        
        # 过滤出较长的关键字（>=4字符）并排除年份关键字和黑名单关键字
        long_keywords1 = [k for k in keywords1 if len(k) >= 4 and not is_blacklisted_keyword(k)]
        long_keywords2 = [k for k in keywords2 if len(k) >= 4 and not is_blacklisted_keyword(k)]
        
        # 过滤掉年份关键字
        non_year_long_keywords1 = [k for k in long_keywords1 if not is_year_keyword(k)]
        non_year_long_keywords2 = [k for k in long_keywords2 if not is_year_keyword(k)]
        
        # 如果两个文件都有非年份长关键字，优先基于它们计算相似度
        if non_year_long_keywords1 and non_year_long_keywords2:
            set1 = set(non_year_long_keywords1)
            set2 = set(non_year_long_keywords2)
            
            # 计算共同的非年份长关键字
            intersection = set1 & set2
            union = set1 | set2
            
            # 如果有共同的长关键字（>=8字符），直接判定为相似
            long_common_keywords = [kw for kw in intersection if len(kw) >= 8]
            if long_common_keywords:
                return True
            
            # 如果有共同的中长度关键字（4-7字符），也视为相似
            medium_common_keywords = [kw for kw in intersection if len(kw) >= 4]
            if medium_common_keywords:
                # 确保共同关键字足够多或比例足够高
                if len(medium_common_keywords) >= 2 or (union and len(intersection) / len(union) >= 0.5):
                    return True
        
        # 计算Jaccard相似度（包含所有关键字，但排除年份关键字和黑名单关键字）
        non_year_keywords1 = [k for k in keywords1 if not is_year_keyword(k) and not is_blacklisted_keyword(k)]
        non_year_keywords2 = [k for k in keywords2 if not is_year_keyword(k) and not is_blacklisted_keyword(k)]
        
        set1 = set(non_year_keywords1)
        set2 = set(non_year_keywords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union > 0:
            # 根据文件名长度调整相似度计算
            if len(clean1) > 30 or len(clean2) > 30:
                # 长文件名使用关键字Jaccard相似度
                similarity_ratio = intersection / union
                # 对于长文件名，适当调整阈值，但不过于宽松
                adjusted_threshold = max(0.35, min_similarity_ratio - 0.1)
                if similarity_ratio >= adjusted_threshold:
                    return True
    
    # 计算字符级别的Jaccard相似度（排除年份数字和黑名单关键字）
    def remove_year_chars(text):
        # 移除所有看起来像年份的4位数字
        text_no_year = re.sub(r'19\d{2}|20\d{2}', '', text)
        
        # 移除常见的特殊字符
        text_no_year = re.sub(r'[._-]', '', text_no_year)
        return text_no_year
    
    # 移除年份数字后再计算字符相似度
    processed1 = remove_year_chars(clean1)
    processed2 = remove_year_chars(clean2)
    
    set1 = set(processed1)
    set2 = set(processed2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return False
    
    similarity_ratio = intersection / union
    
    # 对于大文件，适当放宽相似度要求，但保持一定的匹配标准
    avg_size_mb = (file1['size'] + file2['size']) / 2 / (1024 * 1024)
    if avg_size_mb > size_threshold_mb:
        min_similarity_ratio = max(0.35, min_similarity_ratio - 0.15)
    
    # 添加对中文字符相似度的额外检查
    def contains_chinese(text):
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    # 如果两个文件名都包含中文，增加中文匹配的权重，但要求中文部分有较多重叠
    if contains_chinese(clean1) and contains_chinese(clean2):
        # 提取中文部分
        chinese1 = ''.join([c for c in clean1 if '\u4e00' <= c <= '\u9fff'])
        chinese2 = ''.join([c for c in clean2 if '\u4e00' <= c <= '\u9fff'])
        
        if chinese1 and chinese2:
            # 计算中文部分的相似度
            chinese_set1 = set(chinese1)
            chinese_set2 = set(chinese2)
            chinese_intersection = len(chinese_set1 & chinese_set2)
            chinese_union = len(chinese_set1 | chinese_set2)
            
            if chinese_union > 0:
                chinese_similarity = chinese_intersection / chinese_union
                
                # 更严格的中文相似度要求，避免误匹配
                # 只有当中文相似度非常高且有足够多的共同字符时，才降低阈值
                if chinese_similarity > 0.8 and len(chinese_set1 & chinese_set2) >= 2:
                    # 保持较高的最小阈值，避免过度宽松
                    min_similarity_ratio = max(0.4, min_similarity_ratio - 0.1)
                # 如果中文相似度很低，提高阈值以避免误匹配
                elif chinese_similarity < 0.3 and len(chinese_set1 | chinese_set2) > 3:
                    min_similarity_ratio = min(0.8, min_similarity_ratio + 0.1)
    
    return similarity_ratio >= min_similarity_ratio

def is_year_keyword(keyword: str) -> bool:
    """
    判断一个关键字是否为年份
    """
    return keyword.isdigit() and len(keyword) == 4 and 1900 <= int(keyword) <= 2100

def find_similar_file_groups(context: VideoOrganizerContext) -> List[List[Dict[str, Any]]]:
    """
查找相似文件组
    
Args:
        context: 包含文件列表和倒排索引的上下文对象
        
Returns:
        List[List[Dict[str, Any]]]: 相似文件组列表
    """
    file_list = context.file_list
    if not file_list:
        return []
    
    # 标记已处理的文件
    processed = set()
    similar_groups = []
    
    # 为每个文件建立关键词映射，便于后续处理
    file_keywords = {}
    for i, file_info in enumerate(file_list):
        base_name = os.path.splitext(file_info['name'])[0]
        cleaned_name = clean_filename(base_name)
        keywords = context._segment_text(cleaned_name)
        
        # 过滤出较长的关键字（>=4字符）作为主要匹配依据，排除黑名单关键字
        long_keywords = [k for k in keywords if len(k) >= 4 and not is_blacklisted_keyword(k)]
        # 过滤掉年份关键字和黑名单关键字，避免仅因年份相同而误匹配
        non_year_long_keywords = [k for k in long_keywords if not is_year_keyword(k)]
        
        file_keywords[i] = {
            'all': keywords,
            'long': long_keywords,
            'non_year_long': non_year_long_keywords
        }
    
    # 简化的分组算法：直接检查每对文件是否相似
    # 对于每对未处理的文件，检查它们是否相似
    for i in range(len(file_list)):
        if i in processed:
            continue
        
        # 创建一个新组
        group = [file_list[i]]
        processed.add(i)
        
        # 对当前组中的每个文件，寻找相似的未处理文件
        for j in range(i + 1, len(file_list)):
            if j in processed:
                continue
                
            file1 = file_list[i]  # 使用组的第一个文件作为基准
            file2 = file_list[j]
            
            # 检查两个文件是否相似，使用更宽松的相似度阈值
            if are_files_similar(file1, file2, context=context, min_similarity_ratio=0.4):
                # 计算共同的非年份长关键字
                file1_non_year = file_keywords[i]['non_year_long']
                file2_non_year = file_keywords[j]['non_year_long']
                common_non_year = set(file1_non_year) & set(file2_non_year)
                
                # 如果有共同的非年份长关键字，或者直接通过相似度计算
                if common_non_year or are_files_similar(file1, file2, context=context):
                    # 添加到当前组
                    group.append(file2)
                    processed.add(j)
        
        # 只添加包含多个文件的组
        if len(group) > 1:
            # 按大小降序排序，优先保留大文件
            group.sort(key=lambda x: x['size'], reverse=True)
            similar_groups.append(group)
    
    # 更新上下文
    context.update_similar_groups(similar_groups)
    
    logging.info(f"找到{len(similar_groups)}组相似文件")
    return similar_groups