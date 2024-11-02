import re
from datetime import datetime

"""
纯函数工具
无多余依赖项
"""


def get_num_from_str(msg: str) -> list:
    """
    从消息字符串中获取数字列表
    :param msg: 从纯字符串中获取的获取的消息字符串
    :return: 提取到的分块整数
    """
    nums = re.findall(r"\d+", msg)
    return nums


def get_datetime_from_str(datetime_str: str):
    """
    将日期-时间字符串转化回datetime对象
    :param datetime_str:
    :return: datetime_obj
    """
    datetime_len = get_num_from_str(datetime_str)
    param_num = len(datetime_len)
    datetime_format_map = {1: "%Y", 2: "%Y-%m", 3: "%Y-%m-%d", 4: "%Y-%m-%d %H",
                           5: "%Y-%m-%d %H:%M", 6: "%Y-%m-%d %H:%M:%S", 7: "%Y-%m-%d %H:%M:%S.%f"}
    datetime_format = datetime_format_map[param_num]
    datetime_obj = datetime.strptime(datetime_str, datetime_format)
    return datetime_obj


def date_sub(new_time, old_time) -> int:
    """
    计算日期差
    可以接收可格式化日期字符串
    """
    if isinstance(new_time, datetime):
        pass
    else:
        new_time = get_datetime_from_str(new_time)

    if isinstance(old_time, datetime):
        pass
    else:
        old_time = get_datetime_from_str(old_time)

    day = (new_time - old_time).days
    sec = (new_time - old_time).seconds

    return (day * 24 * 60 * 60) + sec

