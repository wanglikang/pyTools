# TidySameVideo 项目架构图

## 1. 模块依赖关系（类图）

```mermaid
classDiagram
    direction TB
    
    class video_organizer {
        +main(directories, output_dir)
        +cli_main_wrapper()
    }
    
    class cli {
        +parse_arguments()
        +main()
        +handle_scan_mode()
        +handle_execute_mode()
    }
    
    class data_processor {
        +scan_directory(directory, extensions)
        +scan_multiple_directories(directories, extensions)
        +create_inverted_index(file_list)
        +are_files_similar(file1, file2, min_similarity_ratio, size_threshold_mb)
        +find_similar_file_groups(file_list, inverted_index)
    }
    
    class task_generator {
        +detect_conflicts(task, existing_tasks)
        +generate_move_tasks(similar_groups, output_dir, strategy)
        +validate_move_tasks(tasks)
        +generate_execution_summary(tasks, conflicts, invalid_tasks)
    }
    
    class parallel_executor {
        +calculate_optimal_workers()
        +execute_move_task(task)
        +parallel_execute_tasks(tasks, max_workers)
    }
    
    class utils {
        +setup_logging(log_file)
        +clean_filename(filename)
        +backup_file(file_path)
        +save_to_json(data, file_path)
        +load_from_json(file_path)
        +export_report(report_data, output_file)
        +check_path_length(path, max_length)
        +sanitize_folder_name(name)
        +generate_folder_name(file_group)
    }
    
    class __init__ {
        - 导出主要功能
    }
    
    video_organizer --> utils : 使用
    video_organizer --> data_processor : 使用
    video_organizer --> task_generator : 使用
    video_organizer --> parallel_executor : 使用
    video_organizer --> cli : 使用
    
    cli --> utils : 使用
    cli --> data_processor : 使用
    cli --> task_generator : 使用
    cli --> parallel_executor : 使用
    
    data_processor --> utils : 使用
    
    task_generator --> utils : 使用
    task_generator --> data_processor : 使用
    
    parallel_executor --> utils : 使用
    
    __init__ --> video_organizer : 导出
    __init__ --> utils : 导出
    __init__ --> data_processor : 导出
    __init__ --> task_generator : 导出
    __init__ --> parallel_executor : 导出
```

## 2. 主要执行流程（时序图）

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as cli模块
    participant VideoOrg as video_organizer模块
    participant DataProc as data_processor模块
    participant TaskGen as task_generator模块
    participant ParExec as parallel_executor模块
    participant Utils as utils模块
    
    %% 初始化阶段
    User->>CLI: 执行命令
    CLI->>Utils: setup_logging()
    
    alt 扫描模式
        CLI->>DataProc: scan_multiple_directories()
        DataProc->>DataProc: scan_directory()
        DataProc->>Utils: clean_filename()
        
        CLI->>DataProc: create_inverted_index()
        CLI->>DataProc: find_similar_file_groups()
        DataProc->>DataProc: are_files_similar()
        
        CLI->>TaskGen: generate_move_tasks()
        TaskGen->>Utils: generate_folder_name()
        TaskGen->>Utils: check_path_length()
        TaskGen->>TaskGen: detect_conflicts()
        
        CLI->>TaskGen: validate_move_tasks()
        CLI->>TaskGen: generate_execution_summary()
        CLI->>Utils: save_to_json()
        
        alt 直接执行模式
            CLI->>ParExec: parallel_execute_tasks()
            ParExec->>ParExec: calculate_optimal_workers()
            loop 每个任务
                ParExec->>ParExec: execute_move_task()
                ParExec->>Utils: backup_file()
            end
            CLI->>Utils: export_report()
        else 仅生成任务
            CLI-->>User: 显示任务摘要
        end
        
    else 执行任务模式
        CLI->>Utils: load_from_json()
        CLI->>ParExec: parallel_execute_tasks()
        ParExec->>ParExec: calculate_optimal_workers()
        loop 每个任务
            ParExec->>ParExec: execute_move_task()
            ParExec->>Utils: backup_file()
        end
        CLI->>Utils: export_report()
    end
    
    CLI-->>User: 返回执行结果
```

## 3. 核心功能模块调用关系图

```mermaid
flowchart TD
    subgraph 用户交互层
        A[用户命令] --> B[cli.py]
        B --> C[参数解析]
    end
    
    subgraph 业务逻辑层
        C --> D[video_organizer.py]
        D --> E[主流程控制]
        E --> F1[数据扫描]
        E --> F2[相似性检测]
        E --> F3[任务生成]
        E --> F4[任务执行]
    end
    
    subgraph 功能模块层
        F1 --> G1[data_processor.py]
        F2 --> G1
        F3 --> G2[task_generator.py]
        F4 --> G3[parallel_executor.py]
        G1 --> G4[utils.py]
        G2 --> G4
        G3 --> G4
    end
    
    subgraph 工具函数层
        G4 --> H1[日志处理]
        G4 --> H2[文件操作]
        G4 --> H3[JSON处理]
        G4 --> H4[路径处理]
    end
    
    subgraph 输出结果
        F4 --> I[执行报告]
        I --> J[用户]
    end
```

## 4. 模块功能概述

### 4.1 utils.py - 工具函数模块
- 提供各种辅助功能，如日志配置、文件清理、备份、JSON处理等
- 为其他所有模块提供基础支持

### 4.2 data_processor.py - 数据处理模块
- 负责扫描目录中的视频文件
- 创建文件索引以便快速查找
- 实现相似文件检测算法
- 将相似文件分组

### 4.3 task_generator.py - 任务生成模块
- 基于相似文件组生成移动任务
- 检测任务冲突
- 验证任务有效性
- 生成执行计划摘要

### 4.4 parallel_executor.py - 并行执行模块
- 计算最佳工作线程数
- 实现单个文件移动任务执行
- 提供并行任务执行框架
- 显示执行进度和结果统计

### 4.5 cli.py - 命令行接口模块
- 解析命令行参数
- 提供多种运行模式（扫描、执行任务）
- 协调各个功能模块的工作流
- 生成和显示报告

### 4.6 video_organizer.py - 主模块
- 提供向后兼容的接口
- 协调各个子模块的调用
- 实现完整的视频整理流程