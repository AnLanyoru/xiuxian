import re
from datetime import datetime

from nonebot.adapters.onebot.v11 import Message

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


def get_strs_from_str(msg: str) -> list:
    """
    从消息字符串中获取字符列表
    :param msg: 从args中获取的消息字符串
    :return: 提取到的字符列表
    """
    strs = re.findall(r"[\u4e00-\u9fa5_a-zA-Z]+", msg)
    return strs


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


def get_paged_msg(msg_list: list, page: int | Message, cmd: str = '该指令', per_page_item: int = 12) -> list:
    """
    翻页化信息
    :param msg_list: 需要翻页化的信息列表
    :param page: 获取的页数
    :param per_page_item: 每页信息
    :param cmd: 指令名称
    :return: 处理后信息列表
    """
    if isinstance(page, Message):
        page_msg = get_num_from_str(page.extract_plain_text())
        page = int(page_msg[0]) if page_msg else 1
    items_all = len(msg_list)
    # 总页数
    page_all = ((items_all // per_page_item) + 1) if (items_all % per_page_item != 0) else (items_all // per_page_item)
    if page_all < page:
        msg = [f"\n{cmd}没有那么多页！！！"]
        return msg
    item_num = page * per_page_item - per_page_item
    item_num_end = item_num + per_page_item
    page_info = [f"第{page}/{page_all}页\n——tips——\n可以发送 {cmd}+页数 来查看更多页！\n"]  # 页面尾
    msg_list = msg_list[item_num:item_num_end] + page_info
    return msg_list


def get_args_num(args: Message | str, no: int = 1) -> int:
    """
    获取消息指令参数中的数字，自动处理报错
    :param args: 消息指令参数
    :param no: 需要第几个数字
    :return: 数字
    """
    args_str = args.extract_plain_text() if isinstance(args, Message) else args
    num_msg = get_num_from_str(args_str)
    try:
        num = int(num_msg[no - 1])
        return num
    except (IndexError, TypeError):
        return 0
