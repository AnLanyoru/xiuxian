import json
from pathlib import Path
import os

from ..xiuxian_limit.limit_database import LimitData, limit_handle


class IMPART_PK(object):
    def get_impart_pk_num(self, user_id):
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        impart_pk_num = limit_dict['impart_pk']
        return impart_pk_num

    def update_impart_pk_num(self, user_id):
        is_pass = limit_handle.update_user_limit(user_id, 4, 1)
        return is_pass

    def re_data(self):
        """
        重置数据
        """
        LimitData().redata_limit_by_key('impart_pk')


impart_pk = IMPART_PK()
