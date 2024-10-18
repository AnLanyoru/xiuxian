import operator
import time
from ..xiuxian_place import Place

try:
    import ujson as json
except ImportError:
    import json
import os
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from nonebot.log import logger
from ..xiuxian_config import XiuConfig, convert_rank
from .. import DRIVER
import threading

DATABASE = Path() / "data" / "xiuxian" / "players_database"
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
                self.lock = threading.Lock()
            logger.opt(colors=True).info(f"<green>限制数据库已连接！</green>")
            self.sql_limit = ["user_id", "stone_exp_up", "send_stone", "receive_stone",
                              "impart_pk", "two_exp_up", "last_time", "state"]
            self.sql_active = ["active_id", "active_msg", "active_player", "last_time",
                               "daily_update"]
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>限制数据库关闭！</green>")

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
      "impart_pk" integer DEFAULT 0
      "two_exp_up" integer DEFAULT 0
      "last_time" TEXT,
      "state" TEXT
      );""")
        try:
            c.execute(f"select count(1) from active")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "active" (
      "active_id" INTEGER NOT NULL,
      "active_msg" TEXT,
      "active_player" TEXT,
      "last_time" TEXT,
      "daily_update" INTEGER DEFAULT 0
      );""")

        for i in self.sql_limit:  # 自动补全
            try:
                c.execute(f"select {i} from user_limit")
            except sqlite3.OperationalError:
                logger.opt(colors=True).info("<yellow>user_limit有字段不存在，开始创建\n</yellow>")
                sql = f"ALTER TABLE user_limit ADD COLUMN {i} INTEGER DEFAULT 0;"
                logger.opt(colors=True).info(f"<green>{sql}</green>")
                c.execute(sql)

        for i in self.sql_active:  # 自动补全
            try:
                c.execute(f"select {i} from active")
            except sqlite3.OperationalError:
                logger.opt(colors=True).info("<yellow>active有字段不存在，开始创建\n</yellow>")
                sql = f"ALTER TABLE active ADD COLUMN {i} INTEGER DEFAULT 0;"
                logger.opt(colors=True).info(f"<green>{sql}</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        LimitData().close()

    # 上面是数据库校验，别动

    def get_limit_by_user_id(self, user_id):
        """
        获取目标用户限制列表
        :param user_id: 用户id
        :return:
        """
        now_time = datetime.now()
        sql = f"select * from user_limit WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, user_id)
        result = cur.fetchone()
        if not result:
            # 如果没有，则初始化
            limit_dict = {}
            for key in self.sql_limit:
                limit_dict[key] = 0
            limit_dict['user_id'] = user_id
            limit_dict['last_time'] = now_time
            return limit_dict
        # 如果有，返回限制字典
        columns = [column[0] for column in cur.description]
        limit_dict = dict(zip(columns, result))
        return limit_dict
        pass

    def get_active_by_id(self, active_id):
        """
        获取活动内容
        :param active_id: 活动id
        :return:
        """
        sql = f"select * from active WHERE active_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, active_id)
        result = cur.fetchone()
        if not result:
            return None
        # 如果有，返回活动字典
        columns = [column[0] for column in cur.description]
        active = dict(zip(columns, result))
        return active
        pass

    def update_limit(self, limit_dict: dict):
        """
        更新用户限制
        :param limit_dict: 限制列表
        :return: result
        """
        now_time = datetime.now()
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        user_id = limit_dict['user_id']
        stone_exp_up = limit_dict['stone_exp_up']
        send_stone = limit_dict['send_stone']
        receive_stone = limit_dict['receive_stone']
        impart_pk = limit_dict['impart_pk']
        two_exp_up = limit_dict['two_exp_up']
        state = limit_dict['state']
        table = self.get_limit_by_user_id(user_id)
        if table:
            # 判断是否存在，存在则update
            sql = (f"UPDATE user_limit set "
                   f"stone_exp_up=?,send_stone=?,receive_stone=? impart_pk=? two_exp_up=? state=? "
                   f"WHERE user_id=?")
            cur.execute(sql, (stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, state, user_id))
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO user_limit (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, last_time, state)
                VALUES (?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (user_id, stone_exp_up, send_stone, receive_stone, impart_pk, two_exp_up, now_time, state))
        self.conn.commit()


@DRIVER.on_shutdown
async def close_db():
    LimitData().close()
