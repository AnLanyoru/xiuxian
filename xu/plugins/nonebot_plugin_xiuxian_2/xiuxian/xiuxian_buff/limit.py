import pickle
from pathlib import Path
import os
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_config import convert_rank
from ..xiuxian_utils.utils import (
    number_to, MyEncoder
)

sql_message = XiuxianDateManage()  # sql类

"""
这个系统是依托答辩，千万别用，会变的不幸
停止维护
10.24
利用pickle序列化大幅提升了性能
"""


# 创建限制对象
class TheLimit:
    def __init__(self):
        self.stone_exp_up = 0  # 已灵石修炼数量
        self.receive_stone = 0  # 已收灵石数量
        self.send_stone = 0  # 已送灵石数量
        self.is_get_gift = {"0": 0, 'world_power': 0}  # 活动奖励领取数量，”key：活动ID“: {value:领取次数}


class LimitInfo(object):
    def __init__(self):
        self.dir_path = Path(__file__).parent
        self.data_path = os.path.join(self.dir_path, "limit.pkl")
        try:
            with open(self.data_path, 'rb') as f:
                self.data = pickle.load(f)
                f.close()
        except:
            self.info = {}
            with open(self.data_path, mode="wb") as f:
                pickle.dump(self.info, f)
                f.close()
            with open(self.data_path, 'rb') as f:
                self.data = pickle.load(f)
                f.close()

    def __save(self):
        """
        :return:保存
        """
        with open(self.data_path, mode="wb") as f:
            pickle.dump(self.data, f)
            f.close()

    def save_limit(self, limit_dict):
        """
        保存limit_info
        """
        self.data = limit_dict
        self.__save()
        return True

    def read_limit_info(self):
        """
        读取limit_info信息
        """
        return self.data


# 检查限制对象方法，将搬迁入数据库
class CheckLimit:
    def __init__(self):
        self.per_rank_give_stone = 1500000  # 每个小境界增加收送灵石上限
        self.per_rank_value = 600000  # 每级物品价值增加
        self.max_stone_exp_up = 100000000  # 灵石修炼上限

    def check_send_stone_limit(self, user_id, stone_prepare_send, limit_dict):
        """
        检查送灵石数量是否超标
        :param user_id: 用户ID
        :param stone_prepare_send: 欲送灵石数量
        :param limit_dict: 限制总字典
        :return: 达到限制返回失败文本，布尔值False，未达限制返回更新后总送灵石数量，布尔值True
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_send_stone_num = user_rank * self.per_rank_give_stone
        had_send_stone_num = limit_dict[user_id].send_stone
        left_send_stone_num = max_send_stone_num - had_send_stone_num
        if stone_prepare_send > left_send_stone_num:
            msg = f"\n道友欲送灵石数量超出今日送灵石上限\n道友今日还可送{number_to(left_send_stone_num)}|{left_send_stone_num}灵石"
            return msg, False
        else:
            had_send_stone_num += stone_prepare_send
            return had_send_stone_num, True

    def check_receive_stone_limit(self, user_id, stone_prepare_receive, limit_dict):
        """
        检查接收灵石是否达到上限
        :param user_id: 用户ID
        :param stone_prepare_receive: 欲接收灵石数量
        :param limit_dict: 限制总字典
        :return: 达到限制返回失败文本，布尔值False，未达限制返回更新后总收灵石数量，布尔值True
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_receive_stone_num = user_rank * self.per_rank_give_stone
        had_receive_stone_num = limit_dict[user_id].receive_stone
        left_receive_stone_num = max_receive_stone_num - had_receive_stone_num
        if stone_prepare_receive >= left_receive_stone_num:
            msg = f"\n道友欲送灵石数量超出对方今日收灵石上限\n对方今日还可收{number_to(left_receive_stone_num)}|{left_receive_stone_num}灵石"
            return msg, False
        else:
            had_receive_stone_num += stone_prepare_receive
            return had_receive_stone_num, True

    def update_receive_stone_limit(self, user_id, new_date, limit_dict):
        """
        更新收灵石数量
        :param user_id: 用户ID
        :param new_date: 新数据
        :param limit_dict: 总限制字典
        :return: 余剩收灵石最大数量
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        limit_dict[user_id].receive_stone = new_date
        max_receive_stone_num = user_rank * self.per_rank_give_stone
        return max_receive_stone_num - new_date

    def update_send_stone_limit(self, user_id, new_date, limit_dict):
        """
        更新送灵石数量
        :param user_id: 用户ID
        :param new_date: 新数据
        :param limit_dict: 总限制字典
        :return: 余剩送灵石最大数量
        """
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info["level"])[0]
        max_send_stone_num = user_rank * self.per_rank_give_stone
        limit_dict[user_id].send_stone = new_date
        return max_send_stone_num - new_date

    def send_stone_check(self, send_user_id, receive_user_id, num, limit_dict) -> tuple[str, bool]:
        """
        检查并操作送灵石数量，成功则修改数值，失败则无事发生
        :param send_user_id: 送灵石用户ID
        :param receive_user_id: 收灵石用户ID
        :param num: 灵石数量
        :param limit_dict: 限制总字典
        :return: 结果消息体，是否通过检查bool值
        """
        try:
            limit_dict[send_user_id]
        except KeyError:
            limit_dict[send_user_id] = TheLimit()
        try:
            limit_dict[receive_user_id]
        except KeyError:
            limit_dict[receive_user_id] = TheLimit()
        receive_user_info = sql_message.get_user_info_with_id(receive_user_id)
        send_user_info = sql_message.get_user_info_with_id(send_user_id)
        result_receive, is_receive_pass = self.check_receive_stone_limit(receive_user_id, num, limit_dict)
        result_send, is_send_pass = self.check_send_stone_limit(send_user_id, num, limit_dict)
        if is_send_pass and is_receive_pass:
            receive_left = self.update_receive_stone_limit(receive_user_id, result_receive, limit_dict)
            send_left = self.update_send_stone_limit(send_user_id, result_send, limit_dict)
            receive_name = receive_user_info["user_name"]
            send_name = send_user_info["user_name"]
            msg = (
                f"{send_name}道友成功赠送{receive_name}道友{number_to(num)}|{num}枚灵石"
                f"\n{send_name}道友今日还可送{number_to(send_left)}|{send_left}枚灵石"
                f"\n{receive_name}道友今日还可收取{number_to(receive_left)}|{receive_left}枚灵石")
            return msg, True
        else:
            receive_msg = result_receive if not is_receive_pass else ""
            send_msg = result_send if not is_send_pass else ""
            msg = send_msg + receive_msg
            return msg, False

    def stone_exp_up_check(self, user_id, num, limit_dict):
        try:
            limit_dict[user_id]
        except KeyError:
            limit_dict[user_id] = TheLimit()
        had_stone_exp_up = limit_dict[user_id].stone_exp_up
        left_stone_exp_up = self.max_stone_exp_up - had_stone_exp_up
        if num <= left_stone_exp_up:
            left_stone_exp_up = self.max_stone_exp_up - had_stone_exp_up - num
            msg = (f"\n余剩灵石修炼限额{number_to(left_stone_exp_up)}/{number_to(self.max_stone_exp_up)}"
                   f"|{left_stone_exp_up}/{self.max_stone_exp_up}")
            had_stone_exp_up += num
            limit_dict[user_id].stone_exp_up = had_stone_exp_up
            return had_stone_exp_up, msg, True
        else:
            msg = (f"无法使用这么多的灵石修炼啦！！"
                   f"\n道友今天已经消耗了{number_to(had_stone_exp_up)}|{had_stone_exp_up}枚灵石进行快速修炼了！"
                   f"\n切莫急于求成，小心道基不稳！！"
                   f"\n余剩灵石修炼限额{number_to(left_stone_exp_up)}/{number_to(self.max_stone_exp_up)}"
                   f"|{left_stone_exp_up}/{self.max_stone_exp_up}")
            return had_stone_exp_up, msg, False
        pass
