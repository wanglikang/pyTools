import os
import sys
import time

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class MediaFile:
    filename: str
    full_path: str

@dataclass
class CoverCandidate:
    cover: MediaFile
    source_type: str  # 'same_dir', 'parent_dir', 'sibling_dir', 'cover_dir'

class VideoCoverMatcher:
    def __init__(self, root_dir=None):
        self.root_dir = root_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.video_extensions = ('.mp4', '.mkv', '.avi', '.mov')
        self.cover_extensions = ('.jpg', '.jpeg', '.png')
        self.cover_keywords = ('封面', '海报', 'cover', 'poster')

    def scan_files(self):
        """扫描视频文件和封面文件"""
        self.videos = []
        self.covers = []
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(self.video_extensions):
                    self.videos.append(MediaFile(file, file_path))
                elif file.lower().endswith(self.cover_extensions):
                    creation_timestamp = time.mktime(time.gmtime(os.path.getctime(file_path)))
                    if creation_timestamp < 1747961571:
                        self.covers.append(MediaFile(file, file_path))
                    else:
                        print('文件的创建时间过晚，应该是属于jellyfin自动生成的，忽略:{}'.format(file))
    
    def get_cover_candidates(self, video):
        """获取视频文件的所有候选封面"""
        candidates = []
        video_dir = os.path.dirname(video.full_path)
        video_name = os.path.splitext(video.filename)[0]
        
        # 1. 同目录封面
        for cover in self.covers:
            if os.path.dirname(cover.full_path) == video_dir:
                candidates.append(CoverCandidate(cover, 'same_dir'))
        
        # 2. 上级目录封面
        parent_dir = os.path.dirname(video_dir)
        if parent_dir != video_dir:  # 不是根目录
            for cover in self.covers:
                if os.path.dirname(cover.full_path) == parent_dir:
                    candidates.append(CoverCandidate(cover, 'parent_dir'))
        
        # 3. 上级目录中的封面文件夹
        if parent_dir != video_dir:
            for dir_name in os.listdir(parent_dir):
                dir_path = os.path.join(parent_dir, dir_name)
                if os.path.isdir(dir_path) and any(kw in dir_name for kw in self.cover_keywords):
                    for cover in self.covers:
                        if os.path.dirname(cover.full_path) == dir_path:
                            candidates.append(CoverCandidate(cover, 'cover_dir'))
        
        # 4. 同级目录
        for dir_name in os.listdir(video_dir):
            dir_path = os.path.join(video_dir, dir_name)
            if os.path.isdir(dir_path) and dir_name != os.path.basename(video_dir):
                for cover in self.covers:
                    if os.path.dirname(cover.full_path) == dir_path:
                        candidates.append(CoverCandidate(cover, 'sibling_dir'))
        
        return candidates
    
    def find_best_match(self, video, candidates):
        """找出最佳匹配的封面"""
        video_name = os.path.splitext(video.filename)[0]
        
        # 1. 完全匹配
        for candidate in candidates:
            cover_name = os.path.splitext(candidate.cover.filename)[0]
            if cover_name == video_name:
                return candidate, 'exact_match'
        
        # 2. 前缀或后缀匹配
        for candidate in candidates:
            cover_name = os.path.splitext(candidate.cover.filename)[0]
            if video_name.startswith(cover_name) or video_name.endswith(cover_name):
                return candidate, 'prefix_suffix_match'
        
        # 3. 相似度匹配
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            cover_name = os.path.splitext(candidate.cover.filename)[0]
            matcher = SequenceMatcher(None, video_name, cover_name)
            ratio = matcher.ratio()
            
            if ratio > best_score:
                best_score = ratio
                best_match = candidate
            elif ratio == best_score and best_score > 0:
                # 相同分数时按来源优先级排序
                source_priority = {'same_dir': 1, 'sibling_dir': 2, 'cover_dir': 3, 'parent_dir': 4}
                if source_priority[candidate.source_type] < source_priority[best_match.source_type]:
                    best_match = candidate
        
        return best_match, 'similarity_match' if best_score > 0 else None
    
    def print_results(self, video, best_match, match_type, candidates):
        """打印匹配结果"""
        print(f"\n视频文件: {video.full_path}")
        print(f"最佳匹配 ({match_type}): {best_match.cover.full_path if best_match else '无'}")
        print("候选封面:")
        
        for candidate in candidates:
            prefix = "  * " if best_match and candidate.cover.filename == best_match.cover.filename else "    "
            print(f"{prefix}{candidate.source_type}: {candidate.cover.full_path}")
        
        # 处理nfo文件
        # if best_match:
            # self.update_nfo_file(video, best_match.cover.full_path)
    
    def update_nfo_file(self, video, cover_path):
        """更新或创建nfo文件"""
        nfo_path = os.path.splitext(video.full_path)[0] + '.nfo'
        
        try:
            if os.path.exists(nfo_path):
                # 修改现有nfo文件
                tree = ET.parse(nfo_path)
                root = tree.getroot()
                
                # 查找或创建thumb元素
                thumb = root.find('thumb')
                if thumb is None:
                    thumb = ET.SubElement(root, 'thumb')
                thumb.text = cover_path
                
                # 格式化XML输出
                ET.indent(tree, space="  ", level=0)
                tree.write(nfo_path, encoding='UTF-8', xml_declaration=True)
                print(f"已更新nfo文件: {nfo_path}")
            else:
                # 创建新的nfo文件
                root = ET.Element('movie')
                ET.SubElement(root, 'title').text = os.path.splitext(video.filename)[0]
                ET.SubElement(root, 'thumb').text = cover_path
                
                tree = ET.ElementTree(root)
                # 格式化XML输出
                ET.indent(tree, space="  ", level=0)
                tree.write(nfo_path, encoding='UTF-8', xml_declaration=True)
                print(f"已创建nfo文件: {nfo_path}")
        except Exception as e:
            print(f"处理nfo文件时出错: {nfo_path}, 错误: {str(e)}")
    
    def run(self):
        """运行匹配流程"""
        self.scan_files()
        
        for video in self.videos:
            candidates = self.get_cover_candidates(video)
            best_match, match_type = self.find_best_match(video, candidates)
            self.print_results(video, best_match, match_type, candidates)

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else None
    matcher = VideoCoverMatcher(root_dir)
    matcher.run()