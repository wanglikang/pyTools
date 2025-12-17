# 文件内容转Word文档工具

## 功能介绍

将指定文件夹下符合特定后缀的文件内容递归写入到Word文档中。每个文件的内容会单独占一页，包含文件路径和内容。

## 依赖安装

需要安装python-docx库：

```bash
pip install python-docx
```

## 使用方法

```bash
python file_to_word.py -f <文件夹路径> -e <后缀列表> -o <输出文件>
```

### 参数说明

- `-f`, `--folder`: 要遍历的文件夹路径（必填）
- `-e`, `--extensions`: 要匹配的文件后缀，多个后缀用逗号分隔，如：`.txt,.py,.md`（必填）
- `-o`, `--output`: 输出的Word文档路径，默认：`file_content.docx`

## 示例

### 示例1：将当前目录下所有txt文件转换为Word文档

```bash
python file_to_word.py -f . -e .txt -o txt_files.docx
```

### 示例2：将指定目录下的py和md文件转换为Word文档

```bash
python file_to_word.py -f D:\projects\my_code -e .py,.md -o code_files.docx
```

## 输出格式

Word文档中每个文件的内容格式如下：

```
文件 X: 文件相对路径
    内容:
    文件的实际内容
```

每个文件内容之间会添加分页符。

## 注意事项

1. 脚本会递归遍历指定文件夹下的所有子文件夹
2. 只处理文本文件，不支持二进制文件
3. 文件编码默认为UTF-8，如果文件编码不同可能会导致读取失败
4. 如果文件读取失败，会在Word文档中记录错误信息