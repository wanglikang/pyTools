import os
import re
import json
import logging
import shutil
from typing import Dict, List, Any, Optional, Union

def setup_logging(log_file: str = "video_organizer.log") -> None:
    """配置日志系统，同时输出到文件和控制台"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def clean_filename(filename: str) -> str:
    """清理文件名，移除特殊字符，保留中文字符"""
    # 移除非中文字符、非英文字符、非数字和非基本符号的字符
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\-_\[\]()\{\}\s.]', '', filename)
    # 替换多个空格为单个空格
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # 移除开头和结尾的空格
    cleaned = cleaned.strip()
    # 移除开头和结尾的点号
    cleaned = cleaned.strip('.')
    return cleaned

def backup_file(file_path: str) -> str:
    """备份文件，返回备份文件路径"""
    if not os.path.exists(file_path):
        logging.warning(f"文件不存在，无法备份: {file_path}")
        return ""
    
    base, ext = os.path.splitext(file_path)
    backup_path = f"{base}_backup{ext}"
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{base}_backup_{counter}{ext}"
        counter += 1
    
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"文件已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"备份文件失败: {str(e)}")
        return ""

def save_to_json(data: Any, file_path: str) -> bool:
    """保存数据到JSON文件"""
    try:
        # 确保目录存在，但处理只提供文件名的情况
        dir_name = os.path.dirname(file_path)
        if dir_name:  # 只有当目录名不为空时才创建目录
            os.makedirs(dir_name, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"数据已保存到: {file_path}")
        return True
    except Exception as e:
        logging.error(f"保存JSON文件失败: {str(e)}")
        return False

def load_from_json(file_path: str) -> Optional[Any]:
    """从JSON文件加载数据"""
    if not os.path.exists(file_path):
        logging.warning(f"JSON文件不存在: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"已从{file_path}加载数据")
        return data
    except Exception as e:
        logging.error(f"加载JSON文件失败: {str(e)}")
        return None

def export_report(report_data: Dict[str, Any], output_file: str = "organization_report.txt") -> bool:
    """导出整理报告到文本文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("视频文件整理报告\n")
            f.write("=" * 50 + "\n\n")
            
            if "summary" in report_data:
                f.write("## 概要信息\n")
                for key, value in report_data["summary"].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            if "moved_files" in report_data:
                f.write(f"## 已移动文件 ({len(report_data['moved_files'])})\n")
                for src, dst in report_data["moved_files"].items():
                    f.write(f"从: {src}\n到: {dst}\n\n")
            
            if "failed_files" in report_data:
                f.write(f"## 移动失败文件 ({len(report_data['failed_files'])})\n")
                for file_path, error in report_data["failed_files"].items():
                    f.write(f"文件: {file_path}\n错误: {error}\n\n")
            
            if "conflicts" in report_data:
                f.write(f"## 文件冲突 ({len(report_data['conflicts'])})\n")
                for conflict_info in report_data["conflicts"]:
                    f.write(f"源文件: {conflict_info['source']}\n")
                    f.write(f"目标位置: {conflict_info['target']}\n")
                    f.write(f"冲突类型: {conflict_info['type']}\n\n")
        
        logging.info(f"报告已导出到: {output_file}")
        return True
    except Exception as e:
        logging.error(f"导出报告失败: {str(e)}")
        return False

def check_path_length(path: str, max_length: int = 260) -> bool:
    """检查路径长度是否超过Windows限制"""
    if len(path) > max_length:
        logging.warning(f"路径长度超过{max_length}字符限制: {path}")
        return False
    return True

def sanitize_folder_name(name: str) -> str:
    """清理文件夹名称，移除不允许的字符"""
    # 移除Windows文件夹名不允许的字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # 移除控制字符
    name = ''.join(char for char in name if ord(char) >= 32)
    
    # 移除末尾的空格和点号
    name = name.rstrip('. ')
    
    # 确保文件夹名不为空
    if not name:
        name = "unnamed_folder"
    
    return name

def generate_folder_name(file_group: List[Dict[str, Any]]) -> str:
    """根据文件组生成文件夹名称"""
    if not file_group:
        return "unknown_group"
    
    # 提取所有文件名（不含扩展名）
    file_names = []
    for file_info in file_group:
        base_name = os.path.splitext(os.path.basename(file_info['path']))[0]
        file_names.append(clean_filename(base_name))
    
    # 尝试找出共同前缀
    common_prefix = os.path.commonprefix(file_names)
    common_prefix = common_prefix.rstrip('-_ ')
    
    if common_prefix and len(common_prefix) > 3:
        folder_name = common_prefix
    else:
        # 如果没有明显的共同前缀，使用第一个文件的名称作为基础
        folder_name = file_names[0][:50]  # 限制长度
    
    return sanitize_folder_name(folder_name)