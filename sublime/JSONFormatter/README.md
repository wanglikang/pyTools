# JSON Formatter for Sublime Text

A plugin that formats JSON strings with three different modes:
1. Standard JSON formatting
2. Escaped JSON string formatting
3. Nested JSON string formatting

## Installation
1. Download the `.sublime-package` file
2. In Sublime Text, go to `Preferences > Browse Packages...`
3. Place the package file in the `Installed Packages` directory
4. Restart Sublime Text

## Usage
- Select JSON text
- Use keyboard shortcuts:
  - Ctrl+Alt+J: Standard JSON
  - Ctrl+Alt+Shift+J: Escaped JSON
  - Ctrl+Alt+N: Nested JSON
- Or use Command Palette: `JSON Formatter` options

Formatted JSON will be copied to clipboard automatically.

## 手动打包，包含.python_version
压缩包里 包含 .python_version 文件，指定python的版本为3.8,否则，sublime text 默认运行的python版本是3.3.7