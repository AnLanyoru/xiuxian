import json
from pathlib import Path
import os

from plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_limit import LimitData, LimitHandle


class IMPART_PK(object):
    def __init__(self):
        self.dir_path = Path(__file__).parent
        self.data_path = os.path.join(self.dir_path, "impart_pk.json")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def __save(self):
        """
        :return:保存
        """
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def get_impart_pk_num(self, user_id):
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        impart_pk_num = limit_dict['impart_pk']
        return impart_pk_num

    def update_impart_pk_num(self, user_id):
        is_pass = LimitHandle().update_user_limit(user_id, 4, 1)
        return is_pass

    def check_user_impart(self, user_id):
        """
        核对用户是否存在
        :param user_id:
        """
        user_id = str(user_id)
        try:
            if self.data[user_id]:
                return True
        except KeyError:
            user_number = len(self.data) + 1
            self.data[user_id] = {"number": user_number, "pk_num": 3, "win_num": 0}
            self.__save()
            return False

    def re_data(self):
        """
        重置数据
        """
        LimitData().redata_limit_by_key('impart_pk')


impart_pk = IMPART_PK()
