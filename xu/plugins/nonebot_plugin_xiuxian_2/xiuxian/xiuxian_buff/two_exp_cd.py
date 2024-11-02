import time
from pathlib import Path
import os

from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_limit import LimitData
from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_limit.limit_database import limit_handle


class TWO_EXP_CD(object):

    def find_user(self, user_id):
        """
        匹配词条
        :param user_id:
        """
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        two_exp_num = limit_dict['two_exp_up']
        return two_exp_num

    def add_user(self, user_id) -> bool:
        """
        加入数据
        :param user_id: qq号
        :return: True or False
        """
        limit_handle.update_user_limit(user_id, 5, 1)
        return True

    def re_data(self):
        """
        重置数据
        """
        LimitData().redata_limit_by_key('two_exp_up')


two_exp_cd = TWO_EXP_CD()
