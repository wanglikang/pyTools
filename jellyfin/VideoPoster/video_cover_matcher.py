import os
import sys
import time
import shutil

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
    directory: str    # 封面所在目录
    video_directory: str  # 视频所在目录
    similarity_score: float = 0.0  # 相似度分数

class VideoCoverMatcher:
    def __init__(self, root_dir=None):
        print('当前文件的绝对路径为：{}'.format(os.path.abspath(__file__)))
        print('当前文件的绝对路径为：{}'.format(os.path.dirname(os.path.abspath(__file__))))
        self.root_dir = root_dir or os.path.dirname(os.path.abspath(__file__))
        print('待处理的目录为：{}'.format(self.root_dir))
        self.video_extensions = ('.mp4', '.mkv', '.avi', '.mov')
        self.cover_extensions = ('.jpg', '.jpeg', '.png')
        self.cover_keywords = ('封面', '海报','图片', 'cover', 'poster')
        self.directory_map = {}  # 目录路径 -> {'videos': [], 'covers': []}

    def scan_files(self):
        """扫描视频文件和封面文件，并建立四种映射关系"""
        self.videos = []
        self.covers = []
        self.video_cover_maps = {}  # 视频文件路径 -> 四种封面映射
        
        # 首先收集所有视频和封面文件
        for root, ddir, files in os.walk(self.root_dir):
            # print('walk.{}'.format(root))
            if not '合集' in root :
                print('忽略 {}'.format(root))
                continue

            print('开始处理目录:{}'.format(root))
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(self.video_extensions):
                    self.videos.append(MediaFile(file, file_path))
                elif file.lower().endswith(self.cover_extensions):
                    creation_timestamp = time.mktime(time.gmtime(os.path.getctime(file_path)))
                    if creation_timestamp < 1748362568:
                        self.covers.append(MediaFile(file, file_path))
                    else:
                        print('文件的创建时间过晚，应该是属于jellyfin自动生成的，忽略:{}'.format(file))

        print('扫描到 {} 个视频文件，{}个封面文件'.format(len(self.videos),len(self.covers)))
        # 为每个视频文件建立四种封面映射
        count = 0
        for video in self.videos:
            print('处理到了 {} / {},{}'.format(count,len(self.videos),video.full_path))
            count = count+1
            video_dir = os.path.dirname(video.full_path)
            video_name = os.path.splitext(video.filename)[0]
            parent_dir = os.path.dirname(video_dir)
            
            # 1. 同目录封面
            same_dir_covers = [
                cover for cover in self.covers 
                if os.path.dirname(cover.full_path) == video_dir
            ]
            
            print('同级目录处理完毕')
            # 2. 子目录封面（一级子目录）
            sub_dir_covers = []
            if os.path.exists(video_dir):
                for dir_name in os.listdir(video_dir):
                    dir_path = os.path.join(video_dir, dir_name)
                    if os.path.isdir(dir_path):
                        sub_dir_covers.extend([
                            cover for cover in self.covers 
                            if os.path.dirname(cover.full_path) == dir_path
                        ])
            
            print('子目录处理完毕')
            # 3. 父目录封面
            parent_dir_covers = []
            if parent_dir != video_dir and os.path.exists(parent_dir):
                parent_dir_covers = [
                    cover for cover in self.covers 
                    if os.path.dirname(cover.full_path) == parent_dir
                ]
            
            print('父级目录处理完毕')
            # 4. 父目录特定子目录封面
            parent_sub_dir_covers = []
            if parent_dir != self.root_dir and os.path.exists(parent_dir):
                for dir_name in os.listdir(parent_dir):
                    dir_path = os.path.join(parent_dir, dir_name)
                    if os.path.isdir(dir_path) and any(kw in dir_name for kw in self.cover_keywords):
                        parent_sub_dir_covers.extend([
                            cover for cover in self.covers 
                            if os.path.dirname(cover.full_path) == dir_path
                        ])
            print('兄弟目录处理完毕')
            # 建立映射关系
            self.video_cover_maps[video.full_path] = {
                'same_dir': same_dir_covers,
                'sub_dir': sub_dir_covers,
                'parent_dir': parent_dir_covers,
                'parent_sub_dir': parent_sub_dir_covers
            }
    
    def get_cover_candidates(self, video):
        """获取视频文件的所有候选封面"""
        if video.full_path not in self.video_cover_maps:
            return []
            
        video_dir = os.path.dirname(video.full_path)
        video_name = os.path.splitext(video.filename)[0]
        cover_maps = self.video_cover_maps[video.full_path]
        
        candidates = []
        
        # 1. 同目录封面
        for cover in cover_maps['same_dir']:
            candidates.append(CoverCandidate(
                cover=cover,
                source_type='same_dir',
                directory=video_dir,
                video_directory=video_dir
            ))
        
        # 2. 子目录封面
        for cover in cover_maps['sub_dir']:
            candidates.append(CoverCandidate(
                cover=cover,
                source_type='sub_dir',
                directory=os.path.dirname(cover.full_path),
                video_directory=video_dir
            ))
        
        # 3. 父目录封面
        for cover in cover_maps['parent_dir']:
            candidates.append(CoverCandidate(
                cover=cover,
                source_type='parent_dir',
                directory=os.path.dirname(cover.full_path),
                video_directory=video_dir
            ))
        
        # 4. 父目录特定子目录封面
        for cover in cover_maps['parent_sub_dir']:
            candidates.append(CoverCandidate(
                cover=cover,
                source_type='parent_sub_dir',
                directory=os.path.dirname(cover.full_path),
                video_directory=video_dir
            ))
        
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
                source_priority = {'same_dir': 1, 'sub_dir': 2, 'parent_dir': 3, 'parent_sub_dir': 4}
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
        
        # 复制封面文件到视频目录
        if best_match:
             self.copy_cover_to_video_dir(video, best_match.cover.full_path)
    
    def update_nfo_file(self, video, cover_path):
        """更新或创建nfo文件"""
        nfo_path = os.path.splitext(video.full_path)[0] + '.nfo'
        #  路径是 movie/art/poster
        try:
            if os.path.exists(nfo_path):
                # 修改现有nfo文件
                tree = ET.parse(nfo_path)
                root = tree.getroot()
                
                # 查找或创建thumb元素
                art = root.find('art')
                if art is None:
                    art = ET.SubElement(root, 'art')
                poster = art.find('poster')
                if poster is None:
                    poster = ET.SubElement(art, 'poster')
                poster.text = cover_path
                
                # 格式化XML输出
                ET.indent(tree, space="  ", level=0)
                tree.write(nfo_path, encoding='UTF-8', xml_declaration=True)
                print(f"已更新nfo文件: {nfo_path}")
            else:
                # 创建新的nfo文件
                root = ET.Element('movie')
                art = ET.SubElement(root, 'art')
                poster = ET.SubElement(art, 'poster')
                poster.text = cover_path
                
                tree = ET.ElementTree(root)
                # 格式化XML输出
                ET.indent(tree, space="  ", level=0)
                tree.write(nfo_path, encoding='UTF-8', xml_declaration=True)
                print(f"已创建nfo文件: {nfo_path}")
        except Exception as e:
            print(f"修改nfo文件时出错: {str(e)}")
            return False        

    def copy_cover_to_video_dir(self, video, cover_path):
        """将封面文件复制到视频文件同目录下，并添加'-poster'后缀"""
        try:
            # 获取封面文件扩展名
            ext = os.path.splitext(cover_path)[1]
            # 构建新文件名
            new_name = os.path.splitext(video.filename)[0] + '-poster' + ext
            # 目标路径
            dest_path = os.path.join(os.path.dirname(video.full_path), new_name)
            
            # 复制文件
            shutil.copy2(cover_path, dest_path)
            print(f"已复制封面文件到: {dest_path}")
            return True
        except Exception as e:
            print(f"复制封面文件时出错: {str(e)}")
            return False
    
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