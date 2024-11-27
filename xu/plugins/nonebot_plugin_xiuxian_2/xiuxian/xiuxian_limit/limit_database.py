import operator
import re
import time

import os
import random
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any
import threading

from ..xiuxian_utils.item_json import items

try:
    from .. import DRIVER
except:
    pass
DATABASE = Path() / "data" / "xiuxian" / "players_database"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


def get_num_from_str(msg) -> list:
    """
    从消息字符串中获取数字列表
    :param msg: 从纯字符串中获取的获取的消息字符串
    :return: 提取到的分块整数
    """
    num = re.findall(r"\d+", msg)
    return num


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
        self.blob_data = ["offset_get", "active_get", "state"]
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
                              "impart_pk", "two_exp_up", "rift_protect",
                              "offset_get", "active_get", "last_time", "state"]
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
      "rift_protect" integer DEFAULT 0,
      "offset_get" BLOB,
      "active_get" BLOB,
      "last_time" TEXT,
      "state" BLOB
      );""")
        try:
            c.execute(f"select rift_protect from user_limit")
        except sqlite3.OperationalError:
            sql = f"ALTER TABLE user_limit ADD COLUMN rift_protect integer DEFAULT 0;"
            c.execute(sql)
        try:
            c.execute(f"select count(1) from active")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "active" (
      "active_id" INTEGER NOT NULL,
      "active_name" TEXT,
      "active_desc" TEXT,
      "state" BLOB,
      "start_time" TEXT,
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
      "start_time" TEXT,
      "last_time" TEXT,
      "daily_update" INTEGER DEFAULT 0
      );""")  # 不检查完整性
        # 下面是数据库修补字段
        # 活动&补偿起始时间数据更新
        new_col_table = ["offset", "active"]
        for table in new_col_table:
            try:
                c.execute(f"select start_time from {table}")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE {table} ADD COLUMN start_time TEXT;"
                c.execute(sql)

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
        date = datetime.now().date()
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

        date = datetime.now().date()
        start_time = str(date.today())  # 标记创建日期
        cur = self.conn.cursor()
        sql = f"""INSERT INTO active (active_id, active_name, active_desc, start_time, last_time, daily_update, state)
                VALUES (?,?,?,?,?,?,?)"""
        cur.execute(sql, (active_id, active_name, active_desc, start_time, last_time, daily_update, state))
        self.conn.commit()

    def offset_make(self, offset_id: int, offset_name: str, offset_desc: str, offset_items: dict,
                    last_time: str, daily_update: int, state=''):
        date = datetime.now().date()
        start_time = str(date.today())  # 标记创建日期
        offset_items = pickle.dumps(offset_items)  # 结构化数据
        cur = self.conn.cursor()
        sql = f"""INSERT INTO offset (offset_id, offset_name, offset_desc, offset_items, start_time, last_time, daily_update, state)
                VALUES (?,?,?,?,?,?,?,?)"""
        cur.execute(sql,
                    (offset_id, offset_name, offset_desc, offset_items, start_time, last_time, daily_update, state))
        self.conn.commit()

    def offset_del(self, offset_id: int):
        cur = self.conn.cursor()
        sql = f"""DELETE FROM offset
                WHERE offset_id={offset_id};"""
        cur.execute(sql)
        self.conn.commit()

    def update_limit_data(self, limit_dict: dict):
        """
        更新用户限制
        :param limit_dict: 限制列表
        :return: result
        """
        date = datetime.now().date()
        now_time = date.today()
        cur = self.conn.cursor()
        user_id = limit_dict['user_id']
        stone_exp_up = limit_dict['stone_exp_up']
        send_stone = limit_dict['send_stone']
        receive_stone = limit_dict['receive_stone']
        impart_pk = limit_dict['impart_pk']
        two_exp_up = limit_dict['two_exp_up']
        rift_protect = limit_dict['rift_protect']
        offset_get = limit_dict['offset_get']
        active_get = limit_dict['active_get']
        state = limit_dict['state']
        offset_get = pickle.dumps(offset_get)  # 结构化数据
        active_get = pickle.dumps(active_get)
        state = pickle.dumps(state)
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
            sql = (f"INSERT INTO user_limit "
                   f"(user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, rift_protect, "
                   f"offset_get, active_get, last_time, state) VALUES (?,?,?,?,?,?,?,?,?,?,?)")
            cur.execute(sql, (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, rift_protect,
                              offset_get, active_get, now_time, state))
        self.conn.commit()

    def update_limit_data_with_key(self, limit_dict: dict, update_key: str):
        """
        定向值更新用户限制
        :param update_key: 欲定向更新的列值
        :param limit_dict: 限制列表
        :return: result
        """
        blob_data = self.blob_data
        date = datetime.now().date()
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
            rift_protect = limit_dict['rift_protect']
            offset_get = limit_dict['offset_get']
            active_get = limit_dict['active_get']
            state = limit_dict['state']
            offset_get = pickle.dumps(offset_get)  # 结构化数据
            active_get = pickle.dumps(active_get)
            state = pickle.dumps(state)
            sql = f"""INSERT INTO user_limit (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, 
            rift_protect, offset_get, active_get, last_time, state)VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, rift_protect,
                              offset_get, active_get, now_time, state))
        self.conn.commit()

    def redata_limit_by_key(self, reset_key):
        date = datetime.now().date()
        now_time = date.today()
        cur = self.conn.cursor()
        sql = f"UPDATE user_limit set {reset_key}=? "
        default_value = 0
        if reset_key in self.blob_data:  # 结构化数据
            default_value = {}
            default_value = pickle.dumps(default_value)

        cur.execute(sql, (default_value,))
        self.conn.commit()


class LimitHandle:
    def __init__(self):
        self.blob_data = LimitData().blob_data
        self.msg_list = ['name', 'desc']
        self.sql_limit = LimitData().sql_limit
        self.keymap = {1: "stone_exp_up", 2: "send_stone", 3: "receive_stone", 4: "impart_pk",
                       5: "two_exp_up", 6: "offset_get", 7: "active_get", 8: "rift_protect"}
        pass

    def get_active_msg(self):
        """活动简要信息"""
        idmap = LimitData().get_active_idmap()
        msg = "\r"
        if idmap:
            for name in idmap:
                msg += f"活动ID：{idmap[name]}  活动名称：{name}\r"
            return msg
        else:
            return None

    def get_offset_list(self):
        """补偿简要列表"""
        idmap = LimitData().get_offset_idmap()
        msg = "\r"
        if idmap:
            for name in idmap:
                msg += f"补偿ID：{idmap[name]}  补偿名称：{name}\r"
            return msg
        else:
            return None

    def change_offset_info_to_msg(self, offset_info):
        """
        格式化补偿数据为友好视图
        :param offset_info:
        :return:
        """
        if offset_info:
            offset_id = offset_info.get("offset_id")
            name = offset_info.get("offset_name")
            desc = offset_info.get("offset_desc")
            offset_items = offset_info.get("offset_items")
            last_time = offset_info.get("last_time")
            state = offset_info.get("state")  # 思恋结晶，灵石等补偿数据存放，开发中
            daily_update = offset_info.get("daily_update")
            msg = f"补偿ID：{offset_id}\r补偿名称：{name}\r补偿介绍：{desc}\r"
            if offset_items:
                msg += "包含物品：\r"
                for item_id in offset_items:
                    msg += f"物品：{items.items.get(str(item_id), {}).get('name', '不存在的物品')}  物品数量：{offset_items[item_id]}\r"
            msg += f"补偿领取截止时间：{last_time}\r"
            if daily_update:
                msg += "每日刷新领取\r"
            else:
                msg += "只可领取一次\r"
            return msg

    def get_offset_msg(self, offset_id):
        """
        获取单个补偿的详情信息
        :param offset_id:
        :return:
        """
        offset_info = LimitData().get_offset_by_id(offset_id)
        offset_msg = self.change_offset_info_to_msg(offset_info)
        return offset_msg

    def get_all_user_offset_msg(self, user_id) -> list:
        """
        获取用户的所有补偿状态
        :param user_id:
        :return:
        """
        idmap = LimitData().get_offset_idmap()
        offset_list = []
        for offset_name in idmap:
            offset_id = idmap[offset_name]
            is_get_offset = self.check_user_offset(user_id, offset_id)
            offset_msg = self.get_offset_msg(offset_id)
            if is_get_offset:
                offset_msg += "可领取\r"
            else:
                offset_msg += "无法领取\r"
            offset_list.append(offset_msg)
        return offset_list

    def update_user_limit(self, user_id, limit_num: int, update_data: int, update_type: int = 0):
        """
        更新用户限制数据
        :param user_id: 用户ID
        :param limit_num: 更新目标值
        支持的值：1:"stone_exp_up"|2:"send_stone"|3:"receive_stone"|4:"impart_pk"|5:"two_exp_up"|8:"rift_protect"
        :param update_data: 更新的数据
        :param update_type: 更新类型 0为增加 1为减少
        :return: 是否成功
        """
        limit_key = self.keymap[limit_num]  # 懒狗只想打数字
        limit, is_pass = LimitData().get_limit_by_user_id(user_id)
        goal_data = limit[limit_key]
        if update_type:
            update_data = -update_data
        goal_data += update_data
        limit[limit_key] = goal_data
        LimitData().update_limit_data_with_key(limit, limit_key)
        return True

    def reset_daily_limit(self, user_id):
        """
        完全重置状态，包括日志，补偿领取等，不建议使用
        :param user_id:
        :return:
        """
        date = datetime.now().date()
        now_time = date.today()

        limit_dict = {}
        for key in self.sql_limit:
            limit_dict[key] = 0
        limit_dict['user_id'] = user_id
        limit_dict['last_time'] = now_time
        for key in self.blob_data:
            limit_dict[key] = {}
        LimitData().update_limit_data(limit_dict)
        pass

    def update_user_offset(self, user_id, offset_id: int) -> bool | tuple[bool, str]:
        """
        更新用户补偿状态，附带检查限制效果，通过获取参数传出布尔值可直接用于检查限制
        :param user_id: 用户ID
        :param offset_id: 补偿ID
        :return: bool
        """
        date = datetime.now().date()
        now_date = date.today()
        now_date_str = str(now_date)
        object_key = 'offset_get'  # 可变参数，记得修改方法
        offset_info = LimitData().get_offset_by_id(offset_id)
        daily = offset_info['daily_update']  # 是否日刷新
        start_time_str = offset_info['start_time']  # 开始日期
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d") \
            if start_time_str else datetime.now()  # 格式化至time对象
        start_time = start_time.date()
        last_time_str = offset_info['last_time']  # 结束日期
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d")  # 格式化至time对象
        last_time = last_time.date()
        if start_time > now_date:
            msg = "该补偿未开放领取！！！"
            return False, msg
        elif last_time < now_date:
            msg = "该补偿已过期！！！"
            return False, msg

        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        offset_get = limit_dict[object_key]
        try:
            offset_state = offset_get.get(offset_id)
        except AttributeError:
            offset_get = {}
            offset_state = offset_get.get(offset_id)
        if offset_state:
            # 如果有该补偿数据则获取最后日期
            last_act_time = offset_state[1]
            # 格式字符串格式回datetime格式
            last_act_time = datetime.strptime(last_act_time, "%Y-%m-%d")  # 最后领取日期
            last_act_time = last_act_time.date()
            if daily:  # 检查补偿类型
                if now_date == last_act_time:  # 日刷新判断
                    msg = "道友今日已经领取过该补偿啦！！"
                    pass  # 同日则不变
                else:
                    # 非同日则更新
                    offset_state[0] += 1
                    offset_state[1] = now_date_str
                    offset_get[offset_id] = offset_state
                    limit_dict[object_key] = offset_get
                    LimitData().update_limit_data_with_key(limit_dict, object_key)
                    return True, ''  # 返回检查成功
            else:
                # 非日更检查是否为新补偿
                if start_time > last_act_time:
                    # 新补偿覆盖旧补偿数据
                    offset_get[offset_id] = [1, now_date_str]  # 数据为列表形式，格式为，[次数，日期]
                    limit_dict[object_key] = offset_get
                    LimitData().update_limit_data_with_key(limit_dict, object_key)
                    return True, ''  # 返回检查成功
                    pass
                msg = "道友已经领取过该补偿啦！！！！"
                pass
        else:
            # 若无则初始化 返回True
            offset_get[offset_id] = [1, now_date_str]  # 数据为列表形式，格式为，[次数，日期]
            limit_dict[object_key] = offset_get
            LimitData().update_limit_data_with_key(limit_dict, object_key)
            return True, ''  # 返回检查成功
        return False, msg  # 流程均检查失败 返回检查失败

    def check_user_offset(self, user_id, offset_id: int) -> bool:
        """
        仅检查限制，通过获取参数传出布尔值用于检查限制
        :param user_id: 用户ID
        :param offset_id: 补偿ID
        :return: bool
        """
        date = datetime.now().date()
        now_date = date.today()
        object_key = 'offset_get'  # 可变参数，记得修改方法
        offset_info = LimitData().get_offset_by_id(offset_id)
        daily = offset_info['daily_update']  # 是否日刷新
        start_time_str = offset_info['start_time']  # 开始日期
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d") \
            if start_time_str else datetime.now()  # 格式化至time对象
        start_time = start_time.date()
        last_time_str = offset_info['last_time']  # 结束日期
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d")  # 格式化至time对象
        last_time = last_time.date()
        if start_time > now_date or last_time < now_date:
            return False
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        offset_get = limit_dict[object_key]
        offset_state = offset_get.get(offset_id)
        if offset_state:
            # 如果有该补偿数据则获取最后日期
            last_act_time = offset_state[1]
            # 格式字符串格式回datetime格式
            last_act_time = datetime.strptime(last_act_time, "%Y-%m-%d")
            last_act_time = last_act_time.date()
            if daily:  # 检查补偿类型
                if now_date == last_act_time:  # 日刷新判断
                    pass  # 同日则不变
                else:
                    # 非同日则更新
                    return True  # 返回检查成功
            else:
                # 非日更检查是否为新补偿
                if start_time > last_act_time:
                    return True  # 返回检查成功
                    pass
                pass
        else:
            # 若无则初始化 返回True
            return True  # 返回检查成功
        return False  # 流程均检查失败 返回检查失败

    def update_user_log_data(self, user_id, msg_body: str) -> bool:
        """
        写入用户日志信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        now_date = datetime.now()
        now_date = now_date.replace(microsecond=0)
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('log')
        except:
            logs = None
        log_data = "时间：" + str(now_date) + "\r" + msg_body
        if logs:
            logs.append(log_data)
            if len(logs) > 10:
                logs = logs[1:]
        else:
            logs = [log_data]
        try:
            state_dict['log'] = logs
        except:
            state_dict = {'log': logs}
        limit_dict[object_key] = state_dict
        LimitData().update_limit_data_with_key(limit_dict, object_key)
        return True

    def get_user_log_data(self, user_id):
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        logs = state_dict.get('log')
        if logs:
            return logs
        else:
            return None

    def update_user_shop_log_data(self, user_id, msg_body: str) -> bool:
        """
        写入用户日志信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        now_date = datetime.now()
        now_date = now_date.replace(microsecond=0)
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('shop_log')
        except:
            logs = None
        log_data = "时间：" + str(now_date) + "\r" + msg_body
        if logs:
            logs.append(log_data)
            if len(logs) > 10:
                logs = logs[1:]
        else:
            logs = [log_data]
        try:
            state_dict['shop_log'] = logs
        except TypeError:
            state_dict = {'shop_log': logs}
        limit_dict[object_key] = state_dict
        LimitData().update_limit_data_with_key(limit_dict, object_key)
        return True

    def get_user_shop_log_data(self, user_id):
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('shop_log')
        except:
            logs = None
        if logs:
            return logs
        else:
            return None

    def update_user_donate_log_data(self, user_id, msg_body: str) -> bool:
        """
        写入用户周贡献信息
        :param user_id: 用户ID
        :param msg_body: 需要写入的信息
        :return: bool
        """
        # now_date = datetime.now()
        # now_date = now_date.replace(microsecond=0)
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('week_donate_log')
        except:
            logs = None
        logs = logs if logs else 0
        log_data = get_num_from_str(msg_body)
        log_data = int(log_data[-1]) if log_data else 0
        logs += log_data
        try:
            state_dict['week_donate_log'] = logs
        except TypeError:
            state_dict = {'week_donate_log': logs}
        limit_dict[object_key] = state_dict
        LimitData().update_limit_data_with_key(limit_dict, object_key)
        return True

    def get_user_donate_log_data(self, user_id):
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('week_donate_log')
        except:
            logs = None
        if logs:
            return int(logs)
        else:
            return 0

    def update_user_world_power_data(self, user_id, world_power) -> bool:
        """
        写入用户天地精华信息
        :param user_id: 用户ID
        :param world_power:
        :return: bool
        """
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        logs = world_power
        try:
            state_dict['world_power'] = logs
        except TypeError:
            state_dict = {'world_power': logs}
        limit_dict[object_key] = state_dict
        LimitData().update_limit_data_with_key(limit_dict, object_key)
        return True

    def get_user_world_power_data(self, user_id):
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('world_power')
        except:
            logs = None
        if logs:
            return int(logs)
        else:
            return 0

    def get_user_rift_protect(self, user_id):
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        rift_protect = limit_dict['rift_protect']
        return rift_protect

    def get_back_fix_data(self, user_id):
        object_key = 'state'  # 可变参数，记得修改方法
        limit_dict, is_pass = LimitData().get_limit_by_user_id(user_id)
        state_dict = limit_dict[object_key]
        try:
            logs = state_dict.get('back_fix')
        except:
            logs = None
        if logs:
            return int(logs)
        else:
            return 0


limit_handle = LimitHandle()

try:
    @DRIVER.on_shutdown
    async def close_db():
        LimitData().close()
except:
    pass
