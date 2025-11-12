import os
import sys
import logging
from context import VideoOrganizerContext
from data_processor import are_files_similar
from keyword_filter import get_keyword_blacklist, is_blacklisted_keyword

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 测试黑名单加载
def test_blacklist_loading():
    """测试关键字黑名单加载功能"""
    logging.info("测试关键字黑名单加载...")
    blacklist = get_keyword_blacklist()
    
    logging.info(f"成功加载黑名单，共{len(blacklist)}个关键字")
    
    # 测试一些常见关键字是否在黑名单中
    test_keywords = ['mp4', '1080p', 'h264', 'aac', 'season', 'episode', 'the']
    
    for keyword in test_keywords:
        status = "在黑名单中" if is_blacklisted_keyword(keyword) else "不在黑名单中"
        logging.info(f"关键字 '{keyword}': {status}")
    
    return True

# 测试分词和黑名单过滤
def test_segmentation_with_blacklist():
    """测试分词过程中的黑名单过滤"""
    logging.info("测试分词过程中的黑名单过滤...")
    
    context = VideoOrganizerContext()
    
    # 测试一些包含黑名单关键字的文件名
    test_filenames = [
        "复仇者联盟4：终局之战_2019_BluRay_1080p_H264_AAC.mp4",
        "流浪地球.The.Wandering.Earth.2019.HD1080P.X264.AAC.mkv",
        "Game.of.Thrones.S08E06.1080p.WEBRip.x264.mp4"
    ]
    
    for filename in test_filenames:
        logging.info(f"测试文件名: {filename}")
        
        # 清理文件名
        base_name = os.path.splitext(filename)[0]
        
        # 分词
        keywords = context._segment_text(base_name)
        logging.info(f"分词结果: {keywords}")
        
        # 检查黑名单关键字过滤
        non_blacklisted = [k for k in keywords if not is_blacklisted_keyword(k)]
        logging.info(f"过滤后关键字: {non_blacklisted}")
        
        # 验证黑名单关键字是否被识别
        blacklisted_in_result = [k for k in keywords if is_blacklisted_keyword(k)]
        if blacklisted_in_result:
            logging.warning(f"警告：分词结果中仍包含黑名单关键字: {blacklisted_in_result}")
    
    return True

# 测试文件相似度计算中的黑名单过滤
def test_similarity_with_blacklist():
    """测试文件相似度计算中的黑名单过滤"""
    logging.info("测试文件相似度计算中的黑名单过滤...")
    
    context = VideoOrganizerContext()
    
    # 创建测试文件信息
    file1 = {
        'path': 'test1.mp4',
        'name': '复仇者联盟4：终局之战_2019_BluRay_1080p_H264_AAC.mp4',
        'size': 1024 * 1024 * 1000,  # 1GB
        'directory': 'dir1'
    }
    
    file2 = {
        'path': 'test2.mp4',
        'name': '复仇者联盟4：终局之战_2019_BluRay_720p_H264_AC3.mp4',
        'size': 1024 * 1024 * 500,  # 500MB
        'directory': 'dir2'
    }
    
    file3 = {
        'path': 'test3.mp4',
        'name': '流浪地球.The.Wandering.Earth.2019.HD1080P.X264.AAC.mkv',
        'size': 1024 * 1024 * 800,  # 800MB
        'directory': 'dir3'
    }
    
    # 测试相似文件
    is_similar1 = are_files_similar(file1, file2, context)
    logging.info(f"文件1和文件2是否相似: {is_similar1}")
    
    # 测试不相似文件
    is_similar2 = are_files_similar(file1, file3, context)
    logging.info(f"文件1和文件3是否相似: {is_similar2}")
    
    return True

# 运行所有测试
def run_all_tests():
    """运行所有测试"""
    logging.info("开始运行关键字黑名单功能测试...")
    
    try:
        test_blacklist_loading()
        test_segmentation_with_blacklist()
        test_similarity_with_blacklist()
        
        logging.info("所有测试完成！")
        return True
    except Exception as e:
        logging.error(f"测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)