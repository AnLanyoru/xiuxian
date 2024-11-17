from typing import Tuple, Any

from ..xiuxian_limit import LimitData
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_config import convert_rank
from ..xiuxian_utils.utils import number_to

sql_message = XiuxianDateManage()  # sql类

"""
这个系统是依托答辩，千万别用，会变的不幸
停止维护
10.24
利用pickle序列化大幅提升了性能
10.31
重构，写入数据库
"""


# 检查限制对象方法迁入数据库
class CheckLimit:
    def __init__(self):
        self.per_rank_give_stone = 7000000  # 每个小境界增加收送灵石上限
        self.per_rank_value = 600000  # 每级物品价值增加
        self.max_stone_exp_up = 10000000000  # 灵石修炼上限

    def check_send_stone_limit(self, user_id, stone_prepare_send):
        """
        检查送灵石数量是否超标
        :param user_id: 用户ID
        :param stone_prepare_send: 欲送灵石数量
        :return: 达到限制返回失败文本，布尔值False，未达限制返回更新后总送灵石数量，布尔值True
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_send_stone_num = user_rank * self.per_rank_give_stone
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        had_send_stone_num = limit_dict.get("send_stone")
        left_send_stone_num = max_send_stone_num - had_send_stone_num
        if stone_prepare_send > left_send_stone_num:
            msg = f"\n道友欲送灵石数量超出今日送灵石上限\n道友今日还可送{number_to(left_send_stone_num)}|{left_send_stone_num}灵石"
            return msg, False
        else:
            had_send_stone_num += stone_prepare_send
            return had_send_stone_num, True

    def check_receive_stone_limit(self, user_id, stone_prepare_receive):
        """
        检查接收灵石是否达到上限
        :param user_id: 用户ID
        :param stone_prepare_receive: 欲接收灵石数量
        :return: 达到限制返回失败文本，布尔值False，未达限制返回更新后总收灵石数量，布尔值True
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_receive_stone_num = user_rank * self.per_rank_give_stone
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        had_receive_stone_num = limit_dict.get("receive_stone")
        left_receive_stone_num = max_receive_stone_num - had_receive_stone_num
        if stone_prepare_receive > left_receive_stone_num:
            msg = f"\n道友欲送灵石数量超出对方今日收灵石上限\n对方今日还可收{number_to(left_receive_stone_num)}|{left_receive_stone_num}灵石"
            return msg, False
        else:
            had_receive_stone_num += stone_prepare_receive
            return had_receive_stone_num, True

    def update_receive_stone_limit(self, user_id, new_date):
        """
        更新收灵石数量
        :param user_id: 用户ID
        :param new_date: 新数据
        :return: 余剩收灵石最大数量
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        limit_dict["receive_stone"] = new_date
        LimitData().update_limit_data(limit_dict)
        max_receive_stone_num = user_rank * self.per_rank_give_stone
        return max_receive_stone_num - new_date

    def update_send_stone_limit(self, user_id, new_date):
        """
        更新送灵石数量
        :param user_id: 用户ID
        :param new_date: 新数据
        :return: 余剩送灵石最大数量
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_send_stone_num = user_rank * self.per_rank_give_stone
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        limit_dict["send_stone"] = new_date
        LimitData().update_limit_data(limit_dict)
        return max_send_stone_num - new_date

    def send_stone_check(self, send_user_id, receive_user_id, num) -> tuple[str, str, bool]:
        """
        检查并操作送灵石数量，成功则修改数值，失败则无事发生
        :param send_user_id: 送灵石用户ID
        :param receive_user_id: 收灵石用户ID
        :param num: 灵石数量
        :return: 结果消息体，是否通过检查bool值
        """
        receive_user_info = sql_message.get_user_info_with_id(receive_user_id)
        send_user_info = sql_message.get_user_info_with_id(send_user_id)
        result_receive, is_receive_pass = self.check_receive_stone_limit(receive_user_id, num)
        result_send, is_send_pass = self.check_send_stone_limit(send_user_id, num)
        if is_send_pass and is_receive_pass:
            receive_left = self.update_receive_stone_limit(receive_user_id, result_receive)
            send_left = self.update_send_stone_limit(send_user_id, result_send)
            receive_name = receive_user_info["user_name"]
            send_name = send_user_info["user_name"]
            send_msg = f"{send_name}道友成功赠送{receive_name}道友{number_to(num)}|{num}枚灵石"
            limit_msg = (f"\n{send_name}道友今日还可送{number_to(send_left)}|{send_left}枚灵石"
                         f"\n{receive_name}道友今日还可收取{number_to(receive_left)}|{receive_left}枚灵石")
            return send_msg, limit_msg, True
        else:
            receive_msg = result_receive if not is_receive_pass else ""
            send_msg = result_send if not is_send_pass else ""
            limit_msg = send_msg + receive_msg
            return '', limit_msg, False

    def stone_exp_up_check(self, user_id, num):
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        had_stone_exp_up = limit_dict.get("stone_exp_up")
        left_stone_exp_up = self.max_stone_exp_up - had_stone_exp_up
        if num <= left_stone_exp_up:
            left_stone_exp_up = self.max_stone_exp_up - had_stone_exp_up - num
            msg = (f"\n余剩灵石修炼限额{number_to(left_stone_exp_up)}/{number_to(self.max_stone_exp_up)}"
                   f"|{left_stone_exp_up}/{self.max_stone_exp_up}")
            had_stone_exp_up += num
            limit_dict["stone_exp_up"] = had_stone_exp_up
            LimitData().update_limit_data(limit_dict)
            return had_stone_exp_up, msg, True
        else:
            msg = (f"无法使用这么多的灵石修炼啦！！"
                   f"\n道友今天已经消耗了{number_to(had_stone_exp_up)}|{had_stone_exp_up}枚灵石进行快速修炼了！"
                   f"\n切莫急于求成，小心道基不稳！！"
                   f"\n余剩灵石修炼限额{number_to(left_stone_exp_up)}/{number_to(self.max_stone_exp_up)}"
                   f"|{left_stone_exp_up}/{self.max_stone_exp_up}")
            return had_stone_exp_up, msg, False
        pass


def reset_stone_exp_up():
    LimitData().redata_limit_by_key("stone_exp_up")
    return True


def reset_send_stone():
    LimitData().redata_limit_by_key("send_stone")
    LimitData().redata_limit_by_key("receive_stone")
    return True
