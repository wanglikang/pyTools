import os
import sys
from context import VideoOrganizerContext

# 创建测试目录作为输出目录
test_dir = os.path.join(os.path.dirname(__file__), 'test_output')
os.makedirs(test_dir, exist_ok=True)

def test_longer_keywords_segmentation():
    """
    测试优化后的分词功能，验证更长关键字的提取
    """
    print("开始测试更长关键字的分词功能...")
    
    # 创建上下文对象
    context = VideoOrganizerContext(output_dir=test_dir)
    
    # 测试用例：各种混合文本
    test_cases = [
        "复仇者联盟4终局之战AvengersEndgame2019",
        "流浪地球TheWanderingEarth2019科幻大片",
        "鬼灭之刃剧场版无限列车篇DemonSlayer2020",
        "肖申克的救赎TheShawshankRedemption1994经典",
        "黑客帝国TheMatrixNeoTrinity1999动作科幻",
        "千与千寻SpiritedAway宫崎骏2001动画",
        "星际穿越InterstellarCooperMurph2014诺兰",
        "这个杀手不太冷LéonMathilda1994动作剧情",
        "疯狂动物城ZootopiaNickJudy2016迪士尼动画",
        "盗梦空间InceptionCobbMal2010科幻悬疑"
    ]
    
    # 记录结果
    results = []
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test_text}")
        keywords = context._segment_text(test_text)
        
        # 统计关键字长度信息
        keyword_lengths = [len(keyword) for keyword in keywords]
        avg_length = sum(keyword_lengths) / len(keyword_lengths) if keyword_lengths else 0
        max_length = max(keyword_lengths) if keyword_lengths else 0
        
        print(f"分词结果: {keywords}")
        print(f"关键字数量: {len(keywords)}")
        print(f"平均长度: {avg_length:.2f}")
        print(f"最大长度: {max_length}")
        
        # 检查是否提取了较长的关键字
        has_long_keywords = max_length >= 4
        print(f"是否提取了较长关键字(>=4字符): {has_long_keywords}")
        
        results.append({
            'text': test_text,
            'keywords': keywords,
            'keyword_count': len(keywords),
            'avg_length': avg_length,
            'max_length': max_length,
            'has_long_keywords': has_long_keywords
        })
    
    # 总结
    print("\n" + "="*50)
    print("测试总结:")
    all_has_long = all(r['has_long_keywords'] for r in results)
    avg_keyword_count = sum(r['keyword_count'] for r in results) / len(results)
    avg_max_length = sum(r['max_length'] for r in results) / len(results)
    
    print(f"所有测试用例是否都提取了较长关键字: {all_has_long}")
    print(f"平均关键字数量: {avg_keyword_count:.2f}")
    print(f"平均最大关键字长度: {avg_max_length:.2f}")
    
    if all_has_long:
        print("\n✅ 测试通过: 分词算法成功提取了较长的关键字")
    else:
        print("\n❌ 测试失败: 部分测试用例未能提取足够长的关键字")
        for r in results:
            if not r['has_long_keywords']:
                print(f"  - 失败用例: {r['text']}, 最大长度: {r['max_length']}")
    
    return all_has_long

def test_practical_file_matching():
    """
    测试实际的文件匹配场景，验证分词优化对相似文件查找的影响
    """
    print("\n" + "="*50)
    print("开始测试实际文件匹配场景...")
    
    # 创建上下文对象
    context = VideoOrganizerContext(output_dir=test_dir)
    
    # 导入are_files_similar函数进行直接测试
    from data_processor import are_files_similar
    
    # 测试直接的相似度计算
    print("测试直接相似度计算:")
    
    # 测试用例1：复仇者联盟相关
    file1 = {'name': '复仇者联盟4终局之战AvengersEndgame2019.mp4', 'size': 1000000000, 'directory': 'movies1'}
    file2 = {'name': '复仇者联盟4.Endgame.2019.BD1080p.mp4', 'size': 800000000, 'directory': 'movies2'}
    result1 = are_files_similar(file1, file2, context=context)
    print(f"测试用例1 (复仇者联盟): {'相似' if result1 else '不相似'}")
    
    # 测试用例2：流浪地球相关
    file3 = {'name': '流浪地球TheWanderingEarth2019.mp4', 'size': 900000000, 'directory': 'movies1'}
    file4 = {'name': '流浪地球.2019.科幻大片.HD.mp4', 'size': 700000000, 'directory': 'movies2'}
    result2 = are_files_similar(file3, file4, context=context)
    print(f"测试用例2 (流浪地球): {'相似' if result2 else '不相似'}")
    
    # 测试用例3：鬼灭之刃相关（中文和英文名称）
    file5 = {'name': '鬼灭之刃剧场版无限列车篇.mp4', 'size': 600000000, 'directory': 'anime1'}
    file6 = {'name': 'Demon.Slayer.Mugen.Train.2020.mp4', 'size': 500000000, 'directory': 'anime2'}
    result3 = are_files_similar(file5, file6, context=context)
    print(f"测试用例3 (鬼灭之刃): {'相似' if result3 else '不相似'}")
    
    # 分词验证 - 显示每个测试用例的分词结果
    print("\n分词结果验证:")
    
    # 测试用例1的分词
    keywords1_1 = context._segment_text(os.path.splitext(file1['name'])[0])
    keywords1_2 = context._segment_text(os.path.splitext(file2['name'])[0])
    print(f"\n复仇者联盟文件1分词: {keywords1_1}")
    print(f"复仇者联盟文件2分词: {keywords1_2}")
    common_keywords1 = set(keywords1_1) & set(keywords1_2)
    print(f"共同关键字: {common_keywords1}")
    
    # 测试用例2的分词
    keywords2_1 = context._segment_text(os.path.splitext(file3['name'])[0])
    keywords2_2 = context._segment_text(os.path.splitext(file4['name'])[0])
    print(f"\n流浪地球文件1分词: {keywords2_1}")
    print(f"流浪地球文件2分词: {keywords2_2}")
    common_keywords2 = set(keywords2_1) & set(keywords2_2)
    print(f"共同关键字: {common_keywords2}")
    
    # 模拟文件列表用于倒排索引测试
    mock_files = [file1, file2, file3, file4, file5, file6]
    for i, f in enumerate(mock_files):
        f['path'] = f'movie{i+1}.mp4'
    
    # 设置文件列表
    context.update_file_list(mock_files)
    
    # 创建倒排索引
    index = context.create_inverted_index()
    print(f"\n创建的倒排索引包含 {len(index)} 个关键词")
    
    # 显示部分索引内容
    print("倒排索引部分内容:")
    sorted_keywords = sorted(index.keys(), key=len, reverse=True)
    for i, keyword in enumerate(sorted_keywords[:5]):  # 显示前5个最长的关键字
        file_count = len(index[keyword])
        print(f"  '{keyword}' ({len(keyword)}字符): {file_count}个文件")
    
    # 导入find_similar_file_groups函数
    from data_processor import find_similar_file_groups
    
    # 查找相似文件组
    similar_groups = find_similar_file_groups(context)
    print(f"\n找到 {len(similar_groups)} 组相似文件")
    
    # 显示相似文件组
    for i, group in enumerate(similar_groups):
        print(f"\n相似组 {i+1}:")
        for file_info in group:
            print(f"  - {file_info['name']}")
    
    # 验证匹配结果
    expected_matches = 2  # 期望复仇者联盟和流浪地球匹配，鬼灭之刃中英文可能难以匹配
    success = result1 and result2 and len(similar_groups) >= expected_matches
    
    if success:
        print("\n✅ 测试通过: 相似度计算和文件匹配正常工作")
    else:
        print("\n❌ 测试失败: 相似度计算或文件匹配存在问题")
    
    return success

def main():
    """
    运行所有测试
    """
    print("分词优化测试脚本")
    print("="*50)
    
    # 运行分词测试
    segmentation_success = test_longer_keywords_segmentation()
    
    # 运行文件匹配测试
    matching_success = test_practical_file_matching()
    
    print("\n" + "="*50)
    print("整体测试结果:")
    
    if segmentation_success and matching_success:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("❌ 部分测试失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())