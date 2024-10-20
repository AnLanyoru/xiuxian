import operator
import time
import os
import random
import pickle
import sqlite3
from datetime import datetime, date
from pathlib import Path
import threading
from typing import Tuple, Dict, Any

DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_num = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class LimitData:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    # 单例化数据库连接
    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(LimitData, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        self.blob_data = ["offset_get", "active_get"]
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "limit.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "limit.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            print(f"记录数据库已连接！")
            self.sql_limit = ["user_id", "stone_exp_up", "send_stone", "receive_stone",
                              "impart_pk", "two_exp_up", "offset_get", "active_get", "last_time", "state"]
            self._check_data()

    def close(self):
        self.conn.close()
        print(f"记录数据库关闭！")

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()
        try:
            c.execute(f"select count(1) from user_limit")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "user_limit" (
      "user_id" INTEGER NOT NULL,
      "stone_exp_up" INTEGER DEFAULT 0,
      "send_stone" INTEGER DEFAULT 0,
      "receive_stone" INTEGER DEFAULT 0,
      "impart_pk" integer DEFAULT 0,
      "two_exp_up" integer DEFAULT 0,
      "offset_get" BLOB,
      "active_get" BLOB,
      "last_time" TEXT,
      "state" BLOB
      );""")
        try:
            c.execute(f"select count(1) from active")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "active" (
      "active_id" INTEGER NOT NULL,
      "active_name" TEXT,
      "active_desc" TEXT,
      "state" BLOB,
      "last_time" TEXT,
      "daily_update" INTEGER DEFAULT 0
      );""")
        try:
            c.execute(f"select count(1) from offset")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "offset" (
      "offset_id" INTEGER NOT NULL,
      "offset_name" TEXT,
      "offset_desc" TEXT,
      "offset_items" BLOB,
      "state" BLOB,
      "last_time" TEXT,
      "daily_update" INTEGER DEFAULT 0
      );""")  # 不检查完整性

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        LimitData().close()

    # 上面是数据库校验，别动

    def get_limit_by_user_id(self, user_id) -> tuple[dict[str, int | Any], bool]:
        """
        获取目标用户限制列表
        :param user_id: 用户id
        :return:
        """
        now_time = date.today()
        sql = f"select * from user_limit WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            # 如果没有，则初始化
            limit_dict = {}
            for key in self.sql_limit:
                limit_dict[key] = 0
            limit_dict['user_id'] = user_id
            limit_dict['last_time'] = str(now_time)

            for key in self.blob_data:
                limit_dict[key] = {}
            return limit_dict, False
        # 如果有，返回限制字典
        columns = [column[0] for column in cur.description]
        limit_dict = dict(zip(columns, result))
        for blob_key in self.blob_data:  # 结构化数据读取
            if limit_dict.get(blob_key):
                limit_dict[blob_key] = pickle.loads(limit_dict[blob_key])

        return limit_dict, True
        pass

    def get_active_idmap(self):
        sql = f"SELECT active_name, active_id FROM active"
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        if result:
            result = dict(result)
        return result

    def get_offset_idmap(self):
        sql = f"SELECT offset_name, offset_id FROM offset"
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        if result:
            result = dict(result)
        return result

    def get_active_by_id(self, active_id):
        """
        获取活动内容
        :param active_id: 活动id
        :return:
        """
        sql = f"select * from active WHERE active_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (active_id,))
        result = cur.fetchone()
        if not result:
            return None
        # 如果有，返回活动字典
        columns = [column[0] for column in cur.description]
        active = dict(zip(columns, result))
        return active
        pass

    def get_offset_by_id(self, offset_id):
        """
        获取补偿内容
        :param offset_id: 活动id
        :return:
        """
        sql = f"select * from offset WHERE offset_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (offset_id,))
        result = cur.fetchone()
        if not result:
            return None
        # 如果有，返回补偿字典
        columns = [column[0] for column in cur.description]
        offset = dict(zip(columns, result))
        if offset.get('offset_items'):
            offset['offset_items'] = pickle.loads(offset['offset_items'])
        return offset
        pass

    def active_make(self, active_id: int, active_name: str, active_desc: str,
                    last_time: str, daily_update: int, state=''):
        cur = self.conn.cursor()
        sql = f"""INSERT INTO active (active_id, active_name, active_desc, last_time, daily_update, state)
                VALUES (?,?,?,?,?,?)"""
        cur.execute(sql, (active_id, active_name, active_desc, last_time, daily_update, state))
        self.conn.commit()

    def offset_make(self, offset_id: int, offset_name: str, offset_desc: str, offset_items: dict,
                    last_time: str, daily_update: int, state=''):
        offset_items = pickle.dumps(offset_items)  # 结构化数据
        cur = self.conn.cursor()
        sql = f"""INSERT INTO offset (offset_id, offset_name, offset_desc, offset_items, last_time, daily_update, state)
                VALUES (?,?,?,?,?,?,?)"""
        cur.execute(sql, (offset_id, offset_name, offset_desc, offset_items, last_time, daily_update, state))
        self.conn.commit()

    def update_limit_data(self, limit_dict: dict):
        """
        更新用户限制
        :param limit_dict: 限制列表
        :return: result
        """
        now_time = date.today()
        cur = self.conn.cursor()
        user_id = limit_dict['user_id']
        stone_exp_up = limit_dict['stone_exp_up']
        send_stone = limit_dict['send_stone']
        receive_stone = limit_dict['receive_stone']
        impart_pk = limit_dict['impart_pk']
        two_exp_up = limit_dict['two_exp_up']
        offset_get = limit_dict['offset_get']
        active_get = limit_dict['active_get']
        offset_get = pickle.dumps(offset_get)  # 结构化数据
        active_get = pickle.dumps(active_get)
        state = limit_dict['state']
        table, is_pass = self.get_limit_by_user_id(user_id)
        if is_pass:
            # 判断是否存在，存在则update
            sql = (f"UPDATE user_limit set "
                   f"stone_exp_up=?,send_stone=?,receive_stone=?,impart_pk=?,two_exp_up=?,"
                   f"offset_get =?,active_get=?,last_time=?,state=? "
                   f"WHERE user_id=?")
            cur.execute(sql, (stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up,
                              offset_get, active_get, now_time, state, user_id))
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO user_limit (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, offset_get, active_get, last_time, state)
                VALUES (?,?,?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up,
                              offset_get, active_get, now_time, state))
        self.conn.commit()

    def update_limit_data_with_key(self, limit_dict: dict, update_key: str):
        """
        定向值更新用户限制
        :param update_key: 欲定向更新的列值
        :param limit_dict: 限制列表
        :return: result
        """
        blob_data = ["offset_get", "active_get"]
        now_time = date.today()
        cur = self.conn.cursor()
        user_id = limit_dict['user_id']
        goal = limit_dict[update_key]
        if update_key in blob_data:  # 结构化数据
            goal = pickle.dumps(goal)
        table, is_pass = self.get_limit_by_user_id(user_id)
        if is_pass:
            # 判断是否存在，存在则update
            sql = f"UPDATE user_limit set {update_key}=? WHERE user_id=?"
            cur.execute(sql, (goal, user_id))
        else:
            # 判断是否存在，不存在则INSERT
            stone_exp_up = limit_dict['stone_exp_up']
            send_stone = limit_dict['send_stone']
            receive_stone = limit_dict['receive_stone']
            impart_pk = limit_dict['impart_pk']
            two_exp_up = limit_dict['two_exp_up']
            offset_get = limit_dict['offset_get']
            active_get = limit_dict['active_get']
            offset_get = pickle.dumps(offset_get)  # 结构化数据
            active_get = pickle.dumps(active_get)
            state = limit_dict['state']
            sql = f"""INSERT INTO user_limit (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, 
            offset_get, active_get, last_time, state)VALUES (?,?,?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up,
                              offset_get, active_get, now_time, state))
        self.conn.commit()


class LimitHandle:
    def __init__(self):
        self.msg_list = ['name', 'desc']
        self.sql_limit = LimitData().sql_limit
        self.keymap = {1: "stone_exp_up", 2: "send_stone", 3: "receive_stone", 4: "impart_pk",
                       5: "two_exp_up", 6: "offset_get", 7: "active_get"}
        pass

    def fast_handle(self):
        now_time = date.today()
        print("欢迎使用快速活动&补偿&限制操作系统\n", "现在是：", now_time, '\n')
        print("请选择你要进行的操作：\n1：操作活动信息\n2：操作补偿信息\n3：操作用户限制信息(making)\n4：进行模拟用户操作(测试用)")
        choice = None
        while choice not in [1, 2, 3, 4]:
            choice = int(input("请选择你要进行的操作:"))
        if choice == 1:
            print("当前已有活动信息：", self.get_active_msg())
            print("请选择你要进行的操作：\n1：添加活动\n2：删除活动(制作中)\n3：修改活动(制作中)\n")
            choice = None
            while choice not in [1, 2, 3]:
                choice = int(input())
            if choice == 1:
                active_id = int(input("请输入活动id："))
                active_name = input("请输入活动名称：")
                active_desc = input("请输入活动介绍：")
                active_deadline = int(input("请输入活动持续时间（天）："))
                last_time = now_time.replace(day=now_time.day + active_deadline)
                active_daily = input("活动是否日刷新奖励（y/n）：")
                active_daily = 0 if active_daily == 'n' else 1
                LimitData().active_make(active_id, active_name, active_desc, str(last_time), active_daily)

                if LimitData().get_active_by_id(active_id):
                    print('创建活动成功！！！')
                else:
                    print("创建活动失败！！")

            pass
        elif choice == 2:
            print("当前已有补偿信息：", self.get_offset_msg())
            print("请选择你要进行的操作：\n1：添加补偿\n2：删除补偿(制作中)\n3：修改补偿(制作中)\n4：查询补偿详情信息\n")
            choice = None
            while choice not in [1, 2, 3, 4]:
                choice = int(input("请输入需要进行的操作id：\n"))
            if choice == 1:
                offset_id = int(input("请输入补偿id："))
                offset_name = input("请输入补偿名称：")
                offset_desc = input("请输入补偿介绍：")
                offset_deadline = int(input("请输入补偿持续时间（天）："))
                last_time = now_time.replace(day=now_time.day + offset_deadline)
                offset_daily = input("补偿是否日刷新奖励（y/n）：")
                offset_daily = 0 if offset_daily == 'n' else 1

                item_num = int(input("补偿物品种类数量："))
                offset_items = {}
                for n in range(item_num):
                    need_item_id = int(input(f"请输入第{n + 1}个补偿物品id:"))
                    need_item_num = int(input(f"请输入第{n + 1}个补偿物品数量:"))
                    offset_items[need_item_id] = need_item_num
                LimitData().offset_make(offset_id, offset_name, offset_desc, offset_items, str(last_time), offset_daily)

                if LimitData().get_offset_by_id(offset_id):
                    print('创建补偿成功！！！')
                else:
                    print("创建补偿失败！！")
            elif choice == 4:
                offset_id = int(input("请输入你想要查询的补偿id："))
                info = LimitData().get_offset_by_id(offset_id)
                if info:
                    print("查询到如下信息：\n" + self.change_offset_info_to_msg(info))
                else:
                    print("没有相关补偿信息！！")
            pass
        elif choice == 4:
            user_id = int(input("请输入模拟用户id："))
            print("当前用户限制词典：", LimitData().get_limit_by_user_id(user_id))
            print("项目id总览(施工中略显寒酸)", self.keymap)
            choice_type = None
            project_type = 0
            while choice_type is None:
                project_type = int(input("请输入要模拟的项目id：\n1-7观察总表\n"))
                choice_type = self.keymap.get(project_type)
            if project_type < 6:
                self.update_user_limit(user_id, project_type, 1)
            elif project_type < 7:
                print("当前已有补偿信息：", self.get_offset_msg())
                offset_id = int(input("请输入要模拟的补偿id："))
                is_pass = self.update_user_offset(user_id, offset_id)
                if is_pass:
                    print("领取补偿成功")
                else:
                    print('领取补偿失败，请勿重复领取')
            print("模拟成功，当前用户限制词典：", LimitData().get_limit_by_user_id(user_id))

            pass

        else:
            pass

    def get_active_msg(self):
        idmap = LimitData().get_active_idmap()
        msg = "\n"
        if idmap:
            for name in idmap:
                msg += f"活动ID：{idmap[name]}  活动名称：{name}\n"
            return msg
        else:
            return None

    def get_offset_msg(self):
        idmap = LimitData().get_offset_idmap()
        msg = "\n"
        if idmap:
            for name in idmap:
                msg += f"补偿ID：{idmap[name]}  补偿名称：{name}\n"
            return msg
        else:
            return None

    def change_offset_info_to_msg(self, offset_info):
        if offset_info:
            offset_id = offset_info.get("offset_id")
            name = offset_info.get("offset_name")
            desc = offset_info.get("offset_desc")
            items = offset_info.get("offset_items")
            last_time = offset_info.get("last_time")
            state = offset_info.get("state")
            daily_update = offset_info.get("daily_update")
            msg = f"补偿ID：{offset_id}\n补偿名称：{name}\n补偿介绍：{desc}\n"
            if items:
                msg += "包含物品：\n"
                for item_id in items:
                    msg += f"物品id：{item_id}  物品数量：{items[item_id]}\n"
            msg += f"补偿领取截止时间：{last_time}(到期补偿记得及时销毁)\n"
            if daily_update:
                msg += "每日刷新领取"
            else:
                msg += "只可领取一次"
            return msg

    def update_user_limit(self, user_id, limit_num: int, update_data: int, update_type: int = 0):
        """
        更新用户限制数据
        :param user_id: 用户ID
        :param limit_num: 更新目标值
        支持的值：1:"stone_exp_up"|2:"send_stone"|3:"receive_stone"|4:"impart_pk"|5:"two_exp_up"
        :param update_data: 更新的数据
        :param update_type: 更新类型 0为增加 1为减少
        :return: 是否成功
        """
        limit_key = self.keymap[limit_num]  # 懒狗只想打数字
        now_date = date.today()
        # day_replace = -1  # 测试日期补正
        # now_date = now_date.replace(day=now_date.day + day_replace)
        now_date = str(now_date)
        limit, is_pass = LimitData().get_limit_by_user_id(user_id)
        last_time = limit['last_time']
        if last_time == now_date:
            goal_data = limit[limit_key]
            pass
        else:
            self.reset_daily_limit(user_id)
            goal_data = 0
        if update_type:
            update_data = -update_data
        goal_data += update_data
        limit[limit_key] = goal_data
        LimitData().update_limit_data_with_key(limit, limit_key)
        return True

    def reset_daily_limit(self, user_id):
        now_time = date.today()

        limit_dict = {}
        for key in self.sql_limit:
            limit_dict[key] = 0
        limit_dict['user_id'] = user_id
        limit_dict['last_time'] = now_time
        LimitData().update_limit_data(limit_dict)
        pass

    def update_user_offset(self, user_id, offset_id: int) -> bool:
        """
        更新用户补偿状态，附带检查限制效果，通过获取参数传出布尔值可直接用于检查限制
        :param user_id: 用户ID
        :param offset_id: 补偿ID
        :return: bool
        """
        now_date = date.today()
        # day_replace = 1  # 测试日期补正
        # now_date = now_date.replace(day=now_date.day + day_replace)
        now_date = str(now_date)
        object_key = 'offset_get'  # 可变参数，记得修改方法
        offset_info = LimitData().get_offset_by_id(offset_id)
        daily = offset_info['daily_update']
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        offset_get = limit_dict[object_key]
        offset_state = offset_get.get(offset_id)
        if offset_state:
            # 如果有该补偿数据则获取最后日期
            if daily:  # 检查补偿类型
                if now_date == offset_state[1]:  # 日刷新判断
                    pass  # 同日则不变
                else:
                    # 非同日则更新
                    offset_state[0] += 1
                    offset_state[1] = now_date
                    offset_get[offset_id] = offset_state
                    limit_dict[object_key] = offset_get
                    LimitData().update_limit_data_with_key(limit_dict, object_key)
                    return True  # 返回检查成功
            else:
                # 非日更直接跳过
                pass
        else:
            # 若无则初始化 返回True
            offset_get[offset_id] = [1, now_date]  # 数据为列表形式，格式为，[次数，日期]
            limit_dict[object_key] = offset_get
            LimitData().update_limit_data_with_key(limit_dict, object_key)
            return True  # 返回检查成功
        return False  # 流程均检查失败 返回检查失败


if __name__ == '__main__':
    while True:
        LimitHandle().fast_handle()
        choice = input("执行结束，任意输入退出")
        if choice:
            break
        else:
            pass
