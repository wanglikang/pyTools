from operator import ne
import sublime
import sublime_plugin
import json
import re
import logging
import sys

# python的版本是3.3.7
class JsonFormatterCommand(sublime_plugin.TextCommand):
    """
    Sublime Text命令，用于格式化JSON字符串
    """
    def run(self, edit,format_type):
        print("python的环境："+sys.version)
        print("format_type:"+format_type)
        # format_type="standard"
        # 获取选中的文本
        regions = self.view.sel()
        for region in regions:
            if region.empty():
                region = sublime.Region(0, self.view.size())
            selected_text = self.view.substr(region)
            print("selected_text:【"+selected_text+"】")
            try:
                # 根据不同类型处理JSON
                if format_type == "escaped":
                    # 处理带转义符的JSON
                    unescaped_text = re.sub(r'\\"', '"', selected_text)
                    json_obj = json.loads(unescaped_text)
                elif format_type == "nested":
                    # 处理嵌套JSON
                    json_obj_str = json.loads(selected_text)
                    # 递归处理嵌套的JSON字符串
                    json_obj = self._process_nested_json(json_obj_str)
                else:
                    # 标准JSON处理
                    json_obj = json.loads(selected_text)
                
                # 格式化JSON
                formatted_json = json.dumps(json_obj, indent=4, ensure_ascii=False)
                
                # 替换选中文本
                self.view.replace(edit, region, formatted_json)
                
                # 复制到剪贴板
                sublime.set_clipboard(formatted_json)
                sublime.status_message("JSON已格式化并复制到剪贴板")
                
            except Exception as e:
                print("error:JSON解析错误: "+selected_text)
                print(">>>>>>>>>>>>")
                logging.exception(e)
                print("<<<<<<<<<<<<")               
                # sublime.error_message("出现错误:{}".format(str(e)))

    def _process_nested_json(self, obj):
        """递归处理嵌套的JSON字符串"""
        if isinstance(obj, dict):
            resultMap = {}
            for key, value in obj.items():
                if isinstance(value, str):
                    try:
                        nested_json = json.loads(value)
                        # obj[key] = nested_json
                        resultMap['__'+key+'__'] = value
                        subResult = self._process_nested_json(nested_json)
                        resultMap[key] = subResult
                    except Exception as e:
                        # print("解析dict中的值异常：key:"+key+",value:"+value)
                        # print(">>>>>>>>>>>>")
                        # logging.exception(e)
                        # print("<<<<<<<<<<<<")
                        resultMap[key] = value
                elif isinstance(value, (dict, list)):
                    subResult = self._process_nested_json(value)
                    resultMap[key] = subResult
                else:
                    resultMap[key] = value
            return resultMap
        elif isinstance(obj, list):
            resultArr = []
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    try:
                        nested_json = json.loads(item)
                        nested_json = self._process_nested_json(nested_json)
                        resultArr.append(nested_json)
                    except Exception as e:
                        # print(f"解析list中的值异常：index:{i},value:{item}")
                        # print("解析list中的值异常：index:"+str(i)+",value:"+item)
                        # print(">>>>>>>>>>>>")
                        # logging.exception(e)
                        # print("<<<<<<<<<<<<")
                        resultArr.append(item)
                elif isinstance(item, (dict, list)):
                    subResult = self._process_nested_json(item)
                    resultArr.append(subResult)
                else:
                     resultArr.append(item)
            return resultArr
        else:
            return obj

    @staticmethod
    def get_selection_from_region(
        region: sublime.Region, regions_length: int, view: sublime.View
    ):
        settings = sublime.load_settings("Pretty JSON.sublime-settings")
        entire_file = False
        if region.empty() and regions_length > 1:
            return None, None
        elif region.empty() and settings.get("use_entire_file_if_no_selection", True):
            region = sublime.Region(0, view.size())
            entire_file = True

        return region, entire_file
