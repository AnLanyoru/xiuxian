from .limit_database import LimitData
from .. import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import UserBuffDate, XIUXIAN_IMPART_BUFF

xiuxian_impart = XIUXIAN_IMPART_BUFF()

# 施工中


class LimitCheck:
    def __init__(self):
        self.two_exp_limit = XiuConfig().two_exp_limit

    def two_exp_limit_check(self, user_id_1, user_id_2) -> tuple[bool, str]:
        user_limit_1, is_pass_1 = LimitData().get_limit_by_user_id(user_id_1)
        user_limit_2, is_pass_2 = LimitData().get_limit_by_user_id(user_id_2)
        user_exp_1 = user_limit_1['two_exp_up']
        user_exp_2 = user_limit_2['two_exp_up']
        # 加入传承
        impart_data_1 = xiuxian_impart.get_user_info_with_id(user_id_1)
        impart_data_2 = xiuxian_impart.get_user_info_with_id(user_id_2)
        impart_two_exp_1 = impart_data_1['impart_two_exp'] if impart_data_1 is not None else 0
        impart_two_exp_2 = impart_data_2['impart_two_exp'] if impart_data_2 is not None else 0

        main_two_data_1 = UserBuffDate(user_id_1).get_user_main_buff_data()  # 功法双修次数提升
        main_two_data_2 = UserBuffDate(user_id_2).get_user_main_buff_data()
        main_two_1 = main_two_data_1['two_buff'] if main_two_data_1 is not None else 0
        main_two_2 = main_two_data_2['two_buff'] if main_two_data_2 is not None else 0
        if user_exp_1 >= (self.two_exp_limit + impart_two_exp_1 + main_two_1):
            msg = "道友今天双修次数已经到达上限！"
            return False, msg
        if user_exp_2 >= (self.two_exp_limit + impart_two_exp_2 + main_two_2):
            msg = "对方今天双修次数已经到达上限！"
            return False, msg
        user_exp_1 += 1
        user_exp_2 += 1
        user_limit_1['two_exp_up'] = user_exp_1
        user_limit_2['two_exp_up'] = user_exp_2
        LimitData().update_limit_data_with_key(user_limit_1, 'two_exp_up')
        LimitData().update_limit_data_with_key(user_limit_2, 'two_exp_up')
        msg = "pass"
        return True, msg
        pass


limit_check = LimitCheck()
