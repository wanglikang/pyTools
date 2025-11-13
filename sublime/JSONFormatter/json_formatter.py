import sublime
import sublime_plugin
import json
import re

class JsonFormatterCommand(sublime_plugin.TextCommand):
    """
    Sublime Text命令，用于格式化JSON字符串
    """
    def run(self, edit, format_type="standard"):
        # 获取选中的文本
        selection = self.view.sel()
        if not selection:
            return

        selected_text = self.view.substr(selection[0])
        
        try:
            # 根据不同类型处理JSON
            if format_type == "escaped":
                # 处理带转义符的JSON
                unescaped_text = re.sub(r'\\"', '"', selected_text)
                json_obj = json.loads(unescaped_text)
            elif format_type == "nested":
                # 处理嵌套JSON
                json_obj = json.loads(selected_text)
                # 递归处理嵌套的JSON字符串
                self._process_nested_json(json_obj)
            else:
                # 标准JSON处理
                json_obj = json.loads(selected_text)
            
            # 格式化JSON
            formatted_json = json.dumps(json_obj, indent=4, ensure_ascii=False)
            
            # 替换选中文本
            self.view.replace(edit, selection[0], formatted_json)
            
            # 复制到剪贴板
            sublime.set_clipboard(formatted_json)
            sublime.status_message("JSON已格式化并复制到剪贴板")
            
        except json.JSONDecodeError as e:
            sublime.error_message(f"JSON解析错误: {str(e)}")
    
    def _process_nested_json(self, obj):
        """递归处理嵌套的JSON字符串"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    try:
                        nested_json = json.loads(value)
                        obj[key] = nested_json
                        self._process_nested_json(nested_json)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(value, (dict, list)):
                    self._process_nested_json(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    try:
                        nested_json = json.loads(item)
                        obj[i] = nested_json
                        self._process_nested_json(nested_json)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(item, (dict, list)):
                    self._process_nested_json(item)