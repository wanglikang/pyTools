# -*- coding: utf-8 -*-  
import sys
import time
import re
import json


class AlfredItems:
    def __init__(self):
        self.items = []

    def add_item(self, uid = '', title = '', subtitle = '', arg = '', valid = True, icon_path = ''):
        """添加一个新的条目到项目列表中"""
        item = {
            "uid": uid,
            "title": title,
            "subtitle": subtitle,
            "arg": arg,
            "icon": {
                "path": icon_path
            }
        }
        self.items.append(item)

    def to_json(self):
        """生成包含所有条目的 JSON 字符串"""
        return json.dumps({"items": self.items}, indent=4)

def getTime(ts, delta=None):
    wf = AlfredItems()
    s = ts
    timeArray = time.localtime(ts)
    
    if delta:
        ts += delta
        timeArray = time.localtime(ts)
    ts = int(ts)
    ms = str(ts*1000)
    wf.add_item(uid = "s", title = "秒: "+str(s), arg=s, valid = True)
    wf.add_item(uid = "ms", title = "毫秒: "+str(ms), arg=ms,  valid = True)
    wf.add_item(uid = "date", title = "日期: "+time.strftime("%Y-%m-%d", timeArray), arg=time.strftime("%Y-%m-%d", timeArray),  valid = True)
    wf.add_item(uid = "datetime", title = "时间: "+time.strftime("%Y-%m-%d %H:%M:%S", timeArray), arg=time.strftime("%Y-%m-%d %H:%M:%S", timeArray),  valid = True)
    print(wf.to_json())


def process_single_input(input_str):
    try:
        delta = 0
        if input_str == 'now':
            ts = time.time()
        elif re.match(r'\d{4}(-|/|\\).*', input_str):
            if re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,9}', input_str):
                timeFormat = "%Y-%m-%d %H:%M:%S.%f"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,6}', input_str):
                timeFormat = "%Y-%m-%d %H:%M:%S.%f"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,3}', input_str):
                timeFormat = "%Y-%m-%d %H:%M:%S.%f"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}:\d{1,2}:\d{1,2}', input_str):
                timeFormat = "%Y-%m-%d %H:%M:%S"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}:\d{1,2}', input_str):
                timeFormat = "%Y-%m-%d %H:%M"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}\W\d{1,2}', input_str):
                timeFormat = "%Y-%m-%d %H"
            elif re.match(r'\d{4}(-|/|\\)\d{1,2}(-|/|\\)\d{1,2}', input_str):
                timeFormat = "%Y-%m-%d"
            elif  re.match(r'\d{4}(-|/|\\)\d{1,2}', input_str):
                timeFormat = "%Y-%m"
            else:
                timeFormat = "%Y-%m-%d %H:%M:%S"

            input_str = re.sub(r'[^\w-]', '-', input_str)
            ts = int(time.mktime(time.strptime(input_str, timeFormat)))
        elif re.match(r'\d+', input_str):
            ts = int(input_str)
            if ts > 253402271999:
                ts = ts / 1000
        elif re.match(r'now.+', input_str):
            # 处理时间运算
            base_time = time.time() if 'now' in input_str else None
          
            matches = re.findall(r'([+-])\s*(\d+)([dhswym])', input_str)
            for sign, num, unit in matches:
                num = int(num)
                if unit == 'd':
                    unit_seconds = 24 * 60 * 60
                elif unit == 'h':
                    unit_seconds = 60 * 60
                elif unit == 's':
                    unit_seconds = 1
                elif unit == 'w':
                    unit_seconds = 7 * 24 * 60 * 60
                elif unit == 'y':
                    unit_seconds = 365 * 24 * 60 * 60
                elif unit == 'm':
                    unit_seconds = 30 * 24 * 60 * 60
                delta += num * unit_seconds if sign == '+' else -num * unit_seconds
            if base_time is not None:
                ts = base_time + delta
            else:
                raise ValueError('不支持的输入格式:'+input_str)
        else:
            return []    
        return [ts,delta]
    except Exception as e:
        print(f'处理输入时出错: {e}')
        return []


if __name__ == '__main__':
    if len(sys.argv) == 1:
        ts = time.time()
        getTime(int(ts)) 
        exit(0)

    query = sys.argv[1]
    ts,delta = process_single_input(query)
    getTime(int(ts))