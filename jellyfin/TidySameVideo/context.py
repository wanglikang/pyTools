import os
import logging
from typing import Dict, List, Any, Optional, Set
import tempfile
import json
import re
from utils import clean_filename
# 导入关键字黑名单功能
from keyword_filter import is_blacklisted_keyword

# 尝试导入分词工具，失败时提供友好提示
try:
    import jieba
    JIEBA_AVAILABLE = True
    logging.info("成功导入jieba中文分词工具")
except ImportError:
    JIEBA_AVAILABLE = False
    logging.warning("未找到jieba中文分词工具，请使用'pip install jieba'安装")

try:
    import MeCab
    MECAB_AVAILABLE = True
    logging.info("成功导入MeCab日文分词工具")
except ImportError:
    MECAB_AVAILABLE = False
    logging.warning("未找到MeCab日文分词工具，请使用'pip install mecab-python3'安装")

class VideoOrganizerContext:
    """
    视频整理工具的上下文管理类
    用于管理和传递各模块间共享的数据和配置
    """
    
    def __init__(self, output_dir: Optional[str] = None, 
                 scan_directories: Optional[List[str]] = None,
                 strategy: str = "keep_best",
                 tasks_file: str = "tasks.json",
                 log_file: str = "video_organizer.log",
                 log_level: str = "info"):
        """
        初始化上下文对象
        
        Args:
            output_dir: 输出目录路径
            scan_directories: 要扫描的目录列表
            strategy: 文件整理策略
            tasks_file: 任务文件保存路径
            log_file: 日志文件路径
            log_level: 日志级别
        """
        self.output_dir = output_dir
        self.scan_directories = scan_directories or []
        self.strategy = strategy
        self.tasks_file = tasks_file
        self.log_file = log_file
        self.log_level = log_level
        
        # 中间数据存储
        self.file_list: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, List[Dict[str, Any]]] = {}
        self.similar_groups: List[List[Dict[str, Any]]] = []
        self.tasks: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, str]] = []
        self.invalid_tasks: List[Dict[str, str]] = []
        self.summary: Dict[str, Any] = {}
    
    def ensure_output_directory(self) -> bool:
        """
        确保输出目录存在
        
        Returns:
            bool: 是否成功创建或验证目录存在
        """
        if not self.output_dir:
            logging.error("未设置输出目录")
            return False
        
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logging.info(f"确保输出目录存在: {self.output_dir}")
            return True
        except Exception as e:
            logging.error(f"创建输出目录失败: {str(e)}")
            return False
    
    def save_inverted_index_to_temp(self) -> Optional[str]:
        """
        保存倒排索引到临时文件
        使用output_dir作为保存目录，如果未设置则使用系统临时目录
        
        Returns:
            Optional[str]: 保存的临时文件路径，如果失败则返回None
        """
        try:
            # 确定保存目录
            dir_path = self.output_dir if self.output_dir else None
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                           suffix='.json', 
                                           encoding='utf-8',
                                           dir=dir_path) as tmp_file:
                # 将文件路径转换为字符串以便序列化
                serializable_index = {}
                for keyword, file_infos in self.inverted_index.items():
                    serializable_index[keyword] = [
                        {k: str(v) if k == 'path' else v for k, v in fi.items()} 
                        for fi in file_infos
                    ]
                json.dump(serializable_index, tmp_file, ensure_ascii=False, indent=2)
                logging.info(f"倒排索引已保存到临时文件: {tmp_file.name}")
                return tmp_file.name
        except Exception as e:
            logging.warning(f"保存倒排索引到临时文件失败: {e}")
            return None
    
    def update_file_list(self, file_list: List[Dict[str, Any]]) -> None:
        """
        更新文件列表
        
        Args:
            file_list: 新的文件列表
        """
        self.file_list = file_list
        logging.info(f"文件列表已更新，共{len(file_list)}个文件")
    
    def update_inverted_index(self, index: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        更新倒排索引
        
        Args:
            index: 新的倒排索引
        """
        self.inverted_index = index
        logging.info(f"倒排索引已更新，包含{len(index)}个关键词")
    
    def update_similar_groups(self, groups: List[List[Dict[str, Any]]]) -> None:
        """
        更新相似文件组
        
        Args:
            groups: 新的相似文件组列表
        """
        self.similar_groups = groups
        logging.info(f"相似文件组已更新，找到{len(groups)}组")
    
    def update_tasks(self, tasks: List[Dict[str, Any]], 
                    conflicts: List[Dict[str, str]],
                    invalid_tasks: List[Dict[str, str]] = None,
                    summary: Dict[str, Any] = None) -> None:
        """
        更新任务信息
        
        Args:
            tasks: 有效任务列表
            conflicts: 冲突列表
            invalid_tasks: 无效任务列表
            summary: 执行摘要
        """
        self.tasks = tasks
        self.conflicts = conflicts
        self.invalid_tasks = invalid_tasks or []
        self.summary = summary or {}
        
        logging.info(f"任务信息已更新，有效任务{len(tasks)}个，冲突{len(conflicts)}个")
    
    def get_task_data(self) -> Dict[str, Any]:
        """
        获取任务数据，用于保存到文件
        
        Returns:
            Dict[str, Any]: 任务数据字典
        """
        return {
            'tasks': self.tasks,
            'conflicts': self.conflicts,
            'invalid_tasks': self.invalid_tasks,
            'summary': self.summary
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要信息
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        return {
            'output_dir': self.output_dir,
            'scan_directories': self.scan_directories,
            'strategy': self.strategy,
            'tasks_file': self.tasks_file,
            'log_level': self.log_level
        }
    
    def _segment_text(self, text: str) -> List[str]:
        """
        对文本进行分词，支持中文、日文和英文，优先选择更长的关键字
        
        Args:
            text: 待分词的文本
            
        Returns:
            List[str]: 分词结果列表，包含较长的关键字
        """
        keywords = []
        processed_positions = set()  # 记录已经处理过的字符位置
        
        # 首先使用正则表达式提取英文字符串
        for match in re.finditer(r'[a-zA-Z]+', text):
            word = match.group()
            if len(word) > 1:  # 忽略单字符英文单词
                keywords.append(word)
                # 记录已处理的位置
                for i in range(match.start(), match.end()):
                    processed_positions.add(i)
        
        # 检测是否包含中文
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', text))
        # 检测是否包含日文
        has_japanese = bool(re.search(r'[\u3040-\u30ff\u3130-\u318f]', text))
        
        # 尝试使用jieba进行中文分词，优先选择更长的词汇
        if has_chinese and JIEBA_AVAILABLE:
            # 使用jieba的搜索引擎模式，获取更多可能的分词结果
            jieba_words = list(jieba.cut_for_search(text)) + list(jieba.cut(text, cut_all=True))
            # 去重并按长度降序排序
            unique_words = list(dict.fromkeys(jieba_words))
            sorted_words = sorted(unique_words, key=lambda x: len(x), reverse=True)
            
            # 优先选择较长的词汇，避免重复处理
            for word in sorted_words:
                # 过滤单字符和纯英文单词
                if len(word) > 1 and not bool(re.match(r'^[a-zA-Z]+$', word)):
                    # 检查单词在原文本中的位置
                    start_pos = text.find(word)
                    if start_pos != -1:
                        # 检查这个单词是否与已处理的位置重叠
                        overlap = False
                        for i in range(start_pos, start_pos + len(word)):
                            if i in processed_positions:
                                overlap = True
                                break
                        
                        if not overlap:
                            keywords.append(word)
                            # 标记此单词占用的位置
                            for i in range(start_pos, start_pos + len(word)):
                                processed_positions.add(i)
        # 尝试使用MeCab进行日文分词
        elif has_japanese and MECAB_AVAILABLE:
            try:
                mecab = MeCab.Tagger("-Owakati")
                japanese_words = mecab.parse(text).strip().split()
                # 按长度降序排序
                sorted_words = sorted(japanese_words, key=lambda x: len(x), reverse=True)
                
                for word in sorted_words:
                    # 过滤单字符和纯英文单词
                    if len(word) > 1 and not bool(re.match(r'^[a-zA-Z]+$', word)):
                        start_pos = text.find(word)
                        if start_pos != -1:
                            # 检查重叠
                            overlap = False
                            for i in range(start_pos, start_pos + len(word)):
                                if i in processed_positions:
                                    overlap = True
                                    break
                            
                            if not overlap:
                                keywords.append(word)
                                for i in range(start_pos, start_pos + len(word)):
                                    processed_positions.add(i)
            except Exception as e:
                logging.warning(f"使用MeCab分词时出错: {e}")
                # 回退到改进的正则表达式，提取更长的连续字符序列
                self._extract_longer_sequences(text, keywords, processed_positions)
        else:
            # 如果没有可用的分词工具，使用改进的正则表达式
            self._extract_longer_sequences(text, keywords, processed_positions)
        
        # 最后，确保所有字符都被处理，提取未被处理的连续字符序列
        self._extract_remaining_sequences(text, keywords, processed_positions)
        
        # 去重并保持顺序
        return list(dict.fromkeys(keywords))
    
    def _extract_longer_sequences(self, text: str, keywords: List[str], 
                                 processed_positions: Set[int]) -> None:
        """
        使用改进的方法提取更长的字符序列
        
        Args:
            text: 原始文本
            keywords: 关键词列表，将添加新提取的关键词
            processed_positions: 已处理的字符位置集合
        """
        # 提取所有可能的中文字符序列，从最长开始尝试
        max_length = len(text)
        for length in range(max_length, 1, -1):  # 从最长到最短
            for i in range(len(text) - length + 1):
                # 跳过已处理的位置
                if i in processed_positions:
                    continue
                
                # 检查这个区间是否包含中文字符
                substring = text[i:i+length]
                if re.search(r'[\u4e00-\u9fa5\u3040-\u30ff\u3130-\u318f]', substring):
                    # 检查整个子串是否都未被处理
                    all_unprocessed = True
                    for j in range(i, i + length):
                        if j in processed_positions:
                            all_unprocessed = False
                            break
                    
                    if all_unprocessed:
                        keywords.append(substring)
                        # 标记为已处理
                        for j in range(i, i + length):
                            processed_positions.add(j)
    
    def _extract_remaining_sequences(self, text: str, keywords: List[str], 
                                   processed_positions: Set[int]) -> None:
        """
        提取未被处理的剩余字符序列
        
        Args:
            text: 原始文本
            keywords: 关键词列表，将添加新提取的关键词
            processed_positions: 已处理的字符位置集合
        """
        i = 0
        while i < len(text):
            # 如果当前位置已处理，跳过
            if i in processed_positions:
                i += 1
                continue
            
            # 找到连续未处理的字符序列
            start = i
            while i < len(text) and i not in processed_positions:
                i += 1
            
            # 获取这个序列
            sequence = text[start:i]
            # 过滤掉空白字符和单字符
            if len(sequence.strip()) > 1:
                keywords.append(sequence.strip())
    
    def create_inverted_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        创建文件名倒排索引，使用分词工具进行更精确的分词，并过滤黑名单关键字
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 倒排索引
        """
        index = {}
        
        for file_info in self.file_list:
            # 获取文件名（不含扩展名）
            base_name = os.path.splitext(file_info['name'])[0]
            cleaned_name = clean_filename(base_name)
            
            # 使用分词工具提取关键字
            keywords = self._segment_text(cleaned_name)
            
            # 添加到索引，但排除黑名单关键字
            for keyword in keywords:
                if len(keyword) > 1 and not is_blacklisted_keyword(keyword):  # 忽略单字符和黑名单关键词
                    if keyword not in index:
                        index[keyword] = []
                    index[keyword].append(file_info)
        
        # 更新到上下文
        self.update_inverted_index(index)
        
        # 保存到临时文件
        self.save_inverted_index_to_temp()
        
        return index

# 已在文件顶部导入re模块