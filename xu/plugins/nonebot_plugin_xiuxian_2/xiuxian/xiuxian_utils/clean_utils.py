import re

"""
纯函数工具
无多余依赖项
"""


def get_num_from_str(msg) -> list:
    """
    从消息字符串中获取数字列表
    :param msg: 从纯字符串中获取的获取的消息字符串
    :return: 提取到的分块整数
    """
    num = re.findall(r"\d+", msg)
    return num
