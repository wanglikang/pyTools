import os
import sys
import argparse
import logging
from typing import List, Optional

# 导入子模块
from utils import setup_logging, load_from_json, save_to_json, export_report
from data_processor import scan_multiple_directories, find_similar_file_groups, create_inverted_index
from task_generator import generate_move_tasks, validate_move_tasks, generate_execution_summary
from parallel_executor import parallel_execute_tasks

def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='视频文件整理工具 - 自动整理相似视频文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    # 扫描模式 - 扫描目录并生成任务文件
    python -m video_organizer --scan "D:/Videos" "E:/Movies" --output "D:/Organized"
    
    # 执行模式 - 执行之前生成的任务
    python -m video_organizer --execute-tasks "tasks.json"
    
    # 扫描并直接执行
    python -m video_organizer --scan "D:/Videos" --output "D:/Organized" --execute
    
    # 指定日志级别
    python -m video_organizer --scan "D:/Videos" --output "D:/Organized" --log-level debug
        """
    )
    
    # 模式选择组
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--scan',
        nargs='+',
        help='要扫描的目录列表'
    )
    mode_group.add_argument(
        '--execute-tasks',
        help='要执行的任务文件路径'
    )
    
    # 输出目录参数
    parser.add_argument(
        '--output',
        help='整理后的输出目录（扫描模式必需）'
    )
    
    # 执行选项
    parser.add_argument(
        '--execute',
        action='store_true',
        help='扫描后直接执行任务（与--scan一起使用）'
    )
    
    # 任务文件保存路径
    parser.add_argument(
        '--tasks-file',
        default='tasks.json',
        help='任务文件保存路径（默认：tasks.json）'
    )
    
    # 日志配置
    parser.add_argument(
        '--log-file',
        default='video_organizer.log',
        help='日志文件路径（默认：video_organizer.log）'
    )
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help='日志级别（默认：info）'
    )
    
    # 高级选项
    parser.add_argument(
        '--strategy',
        choices=['keep_best', 'move_all'],
        default='keep_best',
        help='文件整理策略（默认：keep_best）'
    )
    parser.add_argument(
        '--workers',
        type=int,
        help='并行工作线程数（默认自动计算）'
    )
    
    return parser.parse_args()

def validate_arguments(args: argparse.Namespace) -> bool:
    """验证命令行参数"""
    # 检查扫描模式的参数
    if args.scan:
        # 验证扫描目录是否存在
        for dir_path in args.scan:
            if not os.path.isdir(dir_path):
                print(f"错误: 扫描目录不存在或不是有效的目录: {dir_path}")
                return False
        
        # 验证输出目录参数
        if not args.output:
            print("错误: 扫描模式需要指定输出目录 (--output)")
            return False
    
    # 检查执行任务模式的参数
    if args.execute_tasks:
        if not os.path.isfile(args.execute_tasks):
            print(f"错误: 任务文件不存在: {args.execute_tasks}")
            return False
    
    return True

def handle_scan_mode(args: argparse.Namespace) -> bool:
    """处理扫描模式"""
    print("=== 开始扫描目录 ===")
    
    # 扫描目录
    file_list = scan_multiple_directories(args.scan)
    if not file_list:
        print("未发现任何文件，程序退出")
        return False
    
    print(f"扫描完成，发现 {len(file_list)} 个文件")
    
    # 创建倒排索引
    inverted_index = create_inverted_index(file_list)
    
    # 查找相似文件组
    similar_groups = find_similar_file_groups(file_list, inverted_index)
    if not similar_groups:
        print("未发现相似文件组，无需整理")
        return True
    
    print(f"发现 {len(similar_groups)} 组相似文件")
    
    # 生成移动任务
    tasks, conflicts = generate_move_tasks(similar_groups, args.output, args.strategy)
    
    # 验证任务
    valid_tasks, invalid_tasks = validate_move_tasks(tasks)
    
    # 生成执行摘要
    summary = generate_execution_summary(valid_tasks, conflicts, invalid_tasks)
    
    # 保存任务到文件
    task_data = {
        'tasks': valid_tasks,
        'conflicts': conflicts,
        'invalid_tasks': invalid_tasks,
        'summary': summary
    }
    
    if save_to_json(task_data, args.tasks_file):
        print(f"任务文件已保存到: {args.tasks_file}")
    else:
        print(f"保存任务文件失败: {args.tasks_file}")
        return False
    
    # 打印执行摘要
    print("\n=== 执行计划摘要 ===")
    print(f"总计任务数: {summary['total_tasks']}")
    print(f"冲突数: {summary['conflicts']}")
    print(f"无效任务数: {summary['invalid_tasks']}")
    print(f"估计数据量: {summary['estimated_size_mb']:.2f} MB")
    
    if summary['task_details']:
        print("\n任务预览:")
        for detail in summary['task_details'][:5]:  # 只显示前5个
            if 'note' in detail:
                print(f"  {detail['note']}")
            else:
                print(f"  源: {os.path.basename(detail['source'])}")
                print(f"  目标: {os.path.basename(detail['target'])}")
                print(f"  大小: {detail['size_mb']:.2f} MB")
                print()
    
    # 如果指定了直接执行
    if args.execute and valid_tasks:
        return handle_execute_mode(args.tasks_file, args.workers)
    
    if valid_tasks:
        print(f"\n要执行这些任务，请运行: python -m video_organizer --execute-tasks {args.tasks_file}")
    
    return True

def handle_execute_mode(tasks_file: str, max_workers: Optional[int] = None) -> bool:
    """处理执行任务模式"""
    print("=== 开始执行任务 ===")
    
    # 加载任务文件
    task_data = load_from_json(tasks_file)
    if not task_data or 'tasks' not in task_data:
        print(f"加载任务文件失败或文件格式错误: {tasks_file}")
        return False
    
    tasks = task_data['tasks']
    if not tasks:
        print("任务列表为空，无需执行")
        return True
    
    # 执行任务
    results = parallel_execute_tasks(tasks, max_workers)
    
    # 打印执行结果
    print("\n=== 执行结果 ===")
    print(f"总任务数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    
    if results['failed'] > 0:
        print("\n失败的任务:")
        for file_path, error in list(results['failed_files'].items())[:5]:  # 只显示前5个
            print(f"  {os.path.basename(file_path)}: {error}")
        if len(results['failed_files']) > 5:
            print(f"  ... 还有 {len(results['failed_files']) - 5} 个失败任务")
    
    # 导出报告
    report_data = {
        'summary': {
            '总任务数': results['total'],
            '成功数': results['success'],
            '失败数': results['failed'],
            '成功率': f"{(results['success'] / results['total'] * 100):.2f}%" if results['total'] > 0 else "0%"
        },
        'moved_files': results['moved_files'],
        'failed_files': results['failed_files']
    }
    
    report_file = "organization_report.txt"
    if export_report(report_data, report_file):
        print(f"\n详细报告已导出到: {report_file}")
    
    return results['failed'] == 0

def main() -> int:
    """命令行接口主函数"""
    try:
        # 解析参数
        args = parse_arguments()
        
        # 验证参数
        if not validate_arguments(args):
            return 1
        
        # 设置日志
        setup_logging(args.log_file)
        
        # 设置日志级别
        log_level = getattr(logging, args.log_level.upper())
        logging.getLogger().setLevel(log_level)
        
        # 根据模式处理
        success = False
        if args.scan:
            success = handle_scan_mode(args)
        elif args.execute_tasks:
            success = handle_execute_mode(args.execute_tasks, args.workers)
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        return 1
    except Exception as e:
        print(f"发生错误: {str(e)}")
        logging.exception("未处理的异常")
        return 1

if __name__ == "__main__":
    sys.exit(main())