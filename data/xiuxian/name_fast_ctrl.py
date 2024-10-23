import re

try:
    import ujson as json
except ImportError:
    import json
import sqlite3
from datetime import datetime
from pathlib import Path
import threading
DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_num = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


def get_name_from_str(msg: str) -> list:
    """
    从消息字符串中获取字符列表
    :param msg: 从args中获取的消息字符串
    :return: 提取到的字符列表
    """
    strs = re.findall(r"[\u4e00-\u9fa5_a-zA-Z]+", msg)
    if strs:
        name = strs[0]
    else:
        name = None
    return name


class XiuxianDateManage:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(XiuxianDateManage, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "xiuxian.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "xiuxian.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()

    def close(self):
        self.conn.close()

    @classmethod
    def close_dbs(cls):
        XiuxianDateManage().close()

    def get_user_info_with_id(self, user_id):
        """根据USER_ID获取用户信息,不获取功法加成"""
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian WHERE user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if result:
            columns = [column[0] for column in cur.description]
            user_dict = dict(zip(columns, result))
            return user_dict
        else:
            return None

    def check_user_name(self, user_id):
        user_info = self.get_user_info_with_id(user_id)
        if user_info:
            user_name = user_info.get('user_name')
        else:
            user_name = None
        return user_name

    def update_user_name(self, user_id, user_name):
        """更新用户道号"""
        cur = self.conn.cursor()
        get_name = f"select user_name from user_xiuxian WHERE user_name=?"
        cur.execute(get_name, (user_name,))
        result = cur.fetchone()
        if result:
            return "已存在该道号！", False
        else:
            sql = f"UPDATE user_xiuxian SET user_name=? WHERE user_id=?"

            cur.execute(sql, (user_name, user_id))
            self.conn.commit()
            return f'用户{user_id}的道号更新成功拉~', True

    def main_ctrl(self):
        user_name = None
        user_id = None
        while user_name is None:
            user_id = int(input("输入需要更改的玩家的ID："))
            user_name = self.check_user_name(user_id)
            if user_name is None:
                print(f"不存在ID：{user_id}的玩家！！")
            else:
                is_pass = input(f"请确认需要更改的玩家道号是否为：{user_name}(y/n)")
                pass_map = {"y": 1, "n": 0}
                is_pass = pass_map.get(is_pass)
                if is_pass:
                    pass
                else:
                    user_name = None
        is_pass = False
        while not is_pass:
            new_name = input("输入需要更改的名字：")
            new_name = get_name_from_str(new_name)
            while new_name is None:
                print("请输入合法的名字！！！")
                new_name = input("输入需要更改的名字：")
                new_name = get_name_from_str(new_name)
            result, is_pass = self.update_user_name(user_id, new_name)
            print(result)


if __name__ == "__main__":
    passed = ""
    while not passed:
        XiuxianDateManage().main_ctrl()
        passed = input("任意输入退出，留空继续修改")
