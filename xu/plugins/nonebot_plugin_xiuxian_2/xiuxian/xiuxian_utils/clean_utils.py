import re
from datetime import datetime
import math
import operator
from urllib.parse import quote

from nonebot.adapters.onebot.v11 import Message

from .. import NICKNAME
from .markdown_segment import MessageSegmentPlus

"""
纯函数工具
无多余依赖项
"""


def num_len(num):
    """
    获取数字长度
    :param num:
    :return:
    """
    num = int(num)
    if num:
        if operator.gt(num, 0):
            pass
        else:
            operator.neg(num)
        return operator.add(math.floor(math.log10(num)), 1)
    else:
        return 1


def num_to(num):
    if operator.gt(0, num):
        fh = "-"
    else:
        fh = ''
    digits = num_len(num)
    level = operator.floordiv(digits, 4)
    units = ['', '万', '亿', '万亿', '兆', '万兆', '亿兆', '万亿兆', '京', '万京', '亿京', '万亿京', '兆京', '万兆京',
             '亿兆京',
             '万亿兆京', '垓', '万垓', '亿垓', '万亿垓', '兆垓', '万兆垓', '亿兆垓', '万亿兆垓', '京垓', '万京垓',
             '亿京垓',
             '万亿京垓', '兆京垓', '万兆京垓', '亿兆京垓', '万亿兆京垓', '秭', '万秭', '亿秭', '万亿秭', '兆秭',
             '万兆秭', '亿兆秭',
             '万亿兆秭', '京秭', '万京秭', '亿京秭', '万亿京秭', '兆京秭', '万兆京秭', '亿兆京秭', '万亿兆京秭', '垓秭',
             '万垓秭',
             '亿垓秭', '万亿垓秭', '兆垓秭', '万兆垓秭', '亿兆垓秭', '万亿兆垓秭', '京垓秭', '万京垓秭', '亿京垓秭',
             '万亿京垓秭',
             '兆京垓秭', '万兆京垓秭', '亿兆京垓秭', '万亿兆京垓秭', '壤', '万壤', '亿壤', '万亿壤', '兆壤', '万兆壤',
             '亿兆壤',
             '万亿兆壤', '京壤', '万京壤', '亿京壤', '万亿京壤', '兆京壤', '万兆京壤', '亿兆京壤', '万亿兆京壤', '垓壤',
             '万垓壤',
             '亿垓壤', '万亿垓壤', '兆垓壤', '万兆垓壤', '亿兆垓壤', '万亿兆垓壤', '京垓壤', '万京垓壤', '亿京垓壤',
             '万亿京垓壤',
             '兆京垓壤', '万兆京垓壤', '亿兆京垓壤', '万亿兆京垓壤', '秭壤', '万秭壤', '亿秭壤', '万亿秭壤', '兆秭壤',
             '万兆秭壤',
             '亿兆秭壤', '万亿兆秭壤', '京秭壤', '万京秭壤', '亿京秭壤', '万亿京秭壤', '兆京秭壤', '万兆京秭壤',
             '亿兆京秭壤',
             '万亿兆京秭壤', '垓秭壤', '万垓秭壤', '亿垓秭壤', '万亿垓秭壤', '兆垓秭壤', '万兆垓秭壤', '亿兆垓秭壤',
             '万亿兆垓秭壤',
             '京垓秭壤', '万京垓秭壤', '亿京垓秭壤', '万亿京垓秭壤', '兆京垓秭壤', '万兆京垓秭壤', '亿兆京垓秭壤',
             '万亿兆京垓秭壤', ]
    cost = math.pow(10, operator.sub(operator.mul(4, level), 1))
    last_num = str(operator.floordiv(num, cost))
    return f"{fh}{operator.getitem(last_num, slice(0, -1))}.{operator.getitem(last_num, slice(-1))}{units[level]}"


def number_to(num):
    """
    递归实现，精确为最大单位值 + 小数点后一位
    处理科学计数法表示的数值
    """

    # 处理列表类数据
    if num:
        pass
    else:
        # 打回
        return "零"
    # 处理字符串输入, 你想随意输入为什么不用plus版？
    if isinstance(num, str):
        num = int(num)
    # 处理负数输出
    fh = ""
    if num < 0:
        fh = "-"
        num = abs(num)

    def str_of_size(goal_num, num_level):
        if num_level >= 29:
            return goal_num, num_level
        elif goal_num >= 10000:
            goal_num /= 10000
            num_level += 1
            return str_of_size(goal_num, num_level)
        else:
            return goal_num, num_level

    units = ['', '万', '亿', '万亿', '兆', '万兆', '亿兆', '万亿兆', '京', '万京', '亿京', '万亿京', '兆京', '万兆京',
             '亿兆京',
             '万亿兆京', '垓', '万垓', '亿垓', '万亿垓', '兆垓', '万兆垓', '亿兆垓', '万亿兆垓', '京垓', '万京垓',
             '亿京垓',
             '万亿京垓', '兆京垓', '万兆京垓', '亿兆京垓', '万亿兆京垓', '秭', '万秭', '亿秭', '万亿秭', '兆秭',
             '万兆秭', '亿兆秭',
             '万亿兆秭', '京秭', '万京秭', '亿京秭', '万亿京秭', '兆京秭', '万兆京秭', '亿兆京秭', '万亿兆京秭', '垓秭',
             '万垓秭',
             '亿垓秭', '万亿垓秭', '兆垓秭', '万兆垓秭', '亿兆垓秭', '万亿兆垓秭', '京垓秭', '万京垓秭', '亿京垓秭',
             '万亿京垓秭',
             '兆京垓秭', '万兆京垓秭', '亿兆京垓秭', '万亿兆京垓秭', '壤', '万壤', '亿壤', '万亿壤', '兆壤', '万兆壤',
             '亿兆壤',
             '万亿兆壤', '京壤', '万京壤', '亿京壤', '万亿京壤', '兆京壤', '万兆京壤', '亿兆京壤', '万亿兆京壤', '垓壤',
             '万垓壤',
             '亿垓壤', '万亿垓壤', '兆垓壤', '万兆垓壤', '亿兆垓壤', '万亿兆垓壤', '京垓壤', '万京垓壤', '亿京垓壤',
             '万亿京垓壤',
             '兆京垓壤', '万兆京垓壤', '亿兆京垓壤', '万亿兆京垓壤', '秭壤', '万秭壤', '亿秭壤', '万亿秭壤', '兆秭壤',
             '万兆秭壤',
             '亿兆秭壤', '万亿兆秭壤', '京秭壤', '万京秭壤', '亿京秭壤', '万亿京秭壤', '兆京秭壤', '万兆京秭壤',
             '亿兆京秭壤',
             '万亿兆京秭壤', '垓秭壤', '万垓秭壤', '亿垓秭壤', '万亿垓秭壤', '兆垓秭壤', '万兆垓秭壤', '亿兆垓秭壤',
             '万亿兆垓秭壤',
             '京垓秭壤', '万京垓秭壤', '亿京垓秭壤', '万亿京垓秭壤', '兆京垓秭壤', '万兆京垓秭壤', '亿兆京垓秭壤',
             '万亿兆京垓秭壤', ]
    # 处理科学计数法
    if "e" in str(num):
        num = float(f"{num:.1f}")
    num, level = str_of_size(num, 0)
    if level >= len(units):
        level = len(units) - 1
    final_num = f"{fh}{round(num, 1)}{units[level]}"
    return final_num


def number_to_pro(string):
    """
    快速搜索替换文本内数字到单位制
    :param string:
    :return:
    """
    new_string = re.sub(r'\d+', lambda x: number_to(x.group()), string)
    return new_string


def number_to_msg(string):
    """
    快速搜索替换文本内数字到单位制
    :param string:
    :return:
    """
    new_string = f"{number_to(string)}|{string}"
    return new_string


def number_to_msg_pro(string):
    """
    快速搜索替换文本内数字到单位制
    :param string:
    :return:
    """
    new_string = re.sub(r'\d+', lambda x: f"{number_to(x.group())}|{x.group()}", string)
    return new_string


def number_to_pro_plus(string):
    """
    快速搜索替换数字到单位制
    兼容列表内容，字典值改变
    没事别用这个，需求单纯为什么不去用number_to
    :param string:
    :return:
    """
    if isinstance(string, str):
        new_string = number_to_pro(string)
    elif isinstance(string, list):
        new_string = []
        for msg in string:
            new_string.append(number_to_pro(msg))
    elif isinstance(string, dict):
        for keys in string:
            string[keys] = number_to_pro(string[keys])
        new_string = string
    else:
        new_string = "无"
    return new_string


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


def get_paged_msg(msg_list: list, page: int | Message,
                  cmd: str = '该指令', per_page_item: int = 12, msg_head: str = "") -> list:
    """
    翻页化信息
    :param msg_list: 需要翻页化的信息列表
    :param page: 获取的页数
    :param per_page_item: 每页信息
    :param cmd: 指令名称
    :param msg_head: 可选消息头
    :return: 处理后信息列表
    """
    if isinstance(page, Message):
        page_msg = get_num_from_str(page.extract_plain_text())
        page = int(page_msg[0]) if page_msg else 1
    items_all = len(msg_list)
    # 总页数
    page_all = ((items_all // per_page_item) + 1) if (items_all % per_page_item != 0) else (items_all // per_page_item)
    if page_all < page:
        msg = [f"\r{cmd}没有那么多页！！！"]
        return msg
    item_num = page * per_page_item - per_page_item
    item_num_end = item_num + per_page_item
    msg_head = [msg_head] if msg_head else []
    page_info = [f"第{page}/{page_all}页\r——tips——\r可以发送 {cmd}+页数 来查看更多页！\r"]  # 页面尾
    msg_list = msg_head + msg_list[item_num:item_num_end] + page_info
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


def simple_md(msg_head, inlinecmd,
              inlinecmd_url, msg_end):
    if NICKNAME == "枫林晚":
        return msg_head + inlinecmd + msg_end
    param = [
        {
            "key": "msg_head",
            "values": [f"{msg_head}"]
        },
        {
            "key": "inlinecmd",
            "values": [f"{inlinecmd}"]
        },
        {
            "key": "inlinecmd_url",
            "values": [f"{quote(inlinecmd_url)}"]
        },
        {
            "key": "msg_end",
            "values": [f"{msg_end}"]
        }
    ]
    msg = MessageSegmentPlus.markdown_template("102368631_1732781247", param)
    return msg


def main_md(title, text,
            cmd_see, cmd,
            cmd_see_2, cmd_2,
            cmd_see_3, cmd_3,
            cmd_see_4, cmd_4):
    if NICKNAME == "枫林晚":
        return title + '\r' + text
    param = [
        {
            "key": "title",
            "values": [f"{title}"]
        },
        {
            "key": "text",
            "values": [f"{text}"]
        },
        {
            "key": "cmd_1",
            "values": [f"{cmd_see}"]
        },
        {
            "key": "cmd_1_url",
            "values": [f"{quote(cmd)}"]
        },
        {
            "key": "cmd_2",
            "values": [f"{cmd_see_2}"]
        },
        {
            "key": "cmd_2_url",
            "values": [f"{quote(cmd_2)}"]
        },
        {
            "key": "cmd_3",
            "values": [f"{cmd_see_3}"]
        },
        {
            "key": "cmd_3_url",
            "values": [f"{quote(cmd_3)}"]
        },
        {
            "key": "connect_cmd",
            "values": [f"{cmd_see_4}"]
        },
        {
            "key": "connect_cmd_url",
            "values": [f"{quote(cmd_4)}"]
        }
    ]
    msg = MessageSegmentPlus.markdown_template("102368631_1732506401", param)
    return msg


def help_md(md_id, text):
    if NICKNAME == "枫林晚":
        return text
    param = [
        {
            "key": "text",
            "values": [f"{text}"]
        }
    ]
    msg = MessageSegmentPlus.markdown_template(md_id, param)
    return msg


def msg_handler(*args):

    if len(args) == 3:
        name, uin, msgs = args
        messages = '\r'.join(msgs)
        return messages
    elif len(args) == 1 and isinstance(args[0], list):
        messages = args[0]
        try:
            messages = '\r'.join([str(msg['data']['content']) for msg in messages])
        except TypeError:
            messages = '\r'.join([str(msg) for msg in messages])
        return messages
    else:
        raise ValueError("参数数量或类型不匹配")
