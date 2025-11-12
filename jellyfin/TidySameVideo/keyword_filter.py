import os
import json
import logging
from typing import Set

# 全局黑名单缓存
_keyword_blacklist = None

def load_keyword_blacklist(config_dir: str = None) -> Set[str]:
    """加载关键字黑名单配置
    
    Args:
        config_dir: 配置文件目录，如果为None则使用默认路径
        
    Returns:
        Set[str]: 黑名单关键字集合
    """
    if config_dir is None:
        # 默认配置文件路径
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
    
    blacklist_path = os.path.join(config_dir, 'keyword_blacklist.json')
    
    try:
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 将所有关键字转换为小写并存入集合
            blacklist = {keyword.lower() for keyword in config.get('keywords', [])}
            logging.info(f"成功加载关键字黑名单，共{len(blacklist)}个关键字")
            return blacklist
    except Exception as e:
        logging.warning(f"加载关键字黑名单失败: {str(e)}，将使用空黑名单")
        return set()

def get_keyword_blacklist() -> Set[str]:
    """获取关键字黑名单（使用缓存避免重复加载）"""
    global _keyword_blacklist
    if _keyword_blacklist is None:
        _keyword_blacklist = load_keyword_blacklist()
    return _keyword_blacklist

def is_blacklisted_keyword(keyword: str) -> bool:
    """检查关键字是否在黑名单中（不区分大小写）"""
    return keyword.lower() in get_keyword_blacklist()