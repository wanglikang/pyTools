# 测试数据说明

此目录包含用于测试视频封面匹配功能的测试数据，覆盖各种匹配场景。

## 目录结构

```
test_data/
├── videos/
│   ├── movie1.mp4
│   ├── movie2.mp4
│   └── subfolder/
│       └── movie3.mp4
├── covers/
│   ├── movie1.jpg          # 完全匹配
│   ├── movie2_poster.jpg   # 后缀匹配
│   └── subfolder_movie3.jpg # 前缀匹配
├── 海报文件夹/
│   ├── movie1_poster.png   # 封面文件夹中的匹配
│   └── movie2_cover.jpg    # 封面文件夹中的匹配
└── sibling_folder/
    ├── movie1.jpg          # 同级目录匹配
    └── movie3_cover.jpg    # 同级目录匹配
```

## 测试场景覆盖

1. **完全匹配**：`videos/movie1.mp4` 和 `covers/movie1.jpg`
2. **后缀匹配**：`videos/movie2.mp4` 和 `covers/movie2_poster.jpg`
3. **前缀匹配**：`videos/subfolder/movie3.mp4` 和 `covers/subfolder_movie3.jpg`
4. **封面文件夹匹配**：`videos/` 中的视频与 `海报文件夹/` 中的封面
5. **同级目录匹配**：`videos/` 中的视频与 `sibling_folder/` 中的封面

这些测试数据可以帮助验证脚本在不同情况下的匹配准确性。