import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from nonebot.log import logger
from .. import DRIVER
import threading

from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_place import place
from ..xiuxian_utils.clean_utils import number_to_msg
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.xiuxian2_handle import sql_message

DATABASE = Path() / "data" / "xiuxian" / "items_database"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class UserStoreData:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    # 单例化数据库连接
    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(UserStoreData, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        self.sql_items_table_name = "user_store"
        self.sql_info_table_name = "user_store_info"
        self.sql_col = ["user_id", "need_items_id", "need_items_price", "need_items_num",
                        "need_world", "create_time", "update_time", "sell_user"]
        self.blob_data_list = ["sell_user"]
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "store.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "store.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            logger.opt(colors=True).info(f"<green>商店数据库已连接！</green>")
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>商店数据库关闭！</green>")

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()
        try:
            c.execute(f"select count(1) from {self.sql_info_table_name}")
        except sqlite3.OperationalError:
            c.execute(f"""CREATE TABLE "{self.sql_info_table_name}" (
      "user_id" INTEGER NOT NULL,
      "funds" INTEGER DEFAULT 0
      );""")
        try:
            c.execute(f"select count(1) from {self.sql_items_table_name}")
        except sqlite3.OperationalError:
            c.execute(f"""CREATE TABLE "{self.sql_items_table_name}" (
      "user_id" INTEGER NOT NULL,
      "need_items_id" TEXT NOT NULL,
      "need_items_price" INTEGER DEFAULT 0,
      "need_items_num" INTEGER DEFAULT 0,
      "need_world" INTEGER DEFAULT 0,
      "create_time" TEXT,
      "update_time" TEXT,
      "sell_user" BLOB
      );""")

        for i in self.sql_col:  # 自动补全
            try:
                c.execute(f"select {i} from {self.sql_items_table_name}")
            except sqlite3.OperationalError:
                logger.opt(colors=True).info(f"<yellow>{self.sql_items_table_name}，开始创建\n</yellow>")
                sql = f"ALTER TABLE {self.sql_items_table_name} ADD COLUMN {i} INTEGER DEFAULT 0;"
                logger.opt(colors=True).info(f"<green>{sql}</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        UserStoreData().close()

    # 上面是数据库校验，别动

    def get_user_store_info(self, user_id) -> dict | None:
        """
        获取指定用户商店信息
        :return:
        """
        sql = f"SELECT * FROM {self.sql_info_table_name} WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        user_store_dict = dict(zip(columns, result))
        return user_store_dict

    def user_store_info_make(
            self,
            user_id: int,
            funds: int):
        """
        插入用户商店信息至数据库，数据处理不要放这里
        :param user_id: 玩家ID
        :param funds: 资金
        :return: None
        """
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        item = self.get_user_store_info(user_id)
        if item:
            # 判断是否存在，存在则update
            sql = f"UPDATE {self.sql_info_table_name} set funds=? where user_id=?"
            cur.execute(sql, (funds, user_id))
            is_new = False
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO {self.sql_info_table_name} (user_id, funds) VALUES (?,?)"""
            cur.execute(sql, (user_id, funds))
            is_new = True
        self.conn.commit()
        return is_new

    def get_user_all_want(self, user_id) -> list | None:
        """
        获取指定用户所有求购物品，字典列表输出
        :return:
        """
        sql = f"SELECT * FROM {self.sql_items_table_name} WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchall()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        results = []
        for row in result:
            back_dict = dict(zip(columns, row))
            results.append(back_dict)
        return results

    def get_want_item(self, user_id, item_id):
        """
        获取指定用户的指定求购物品
        :param item_id: 物品id
        :param user_id: 用户id
        :return:
        """
        sql = f"select * from {self.sql_items_table_name} WHERE user_id=? and need_items_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id, item_id))
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        item_dict = dict(zip(columns, result))
        return item_dict

    def del_want_item(self, user_id, item_id):
        """
        获取指定用户的指定求购物品
        :param item_id: 物品id
        :param user_id: 用户id
        :return:
        """
        sql = f"DELETE FROM {self.sql_items_table_name} WHERE user_id=? and need_items_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id, item_id))
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        item_dict = dict(zip(columns, result))
        return item_dict
        pass

    def get_highest_want_item(self, user_id, item_id, sell_item_num):
        """
        获取指定物品的最高求购者
        :param user_id:
        :param sell_item_num: 出售数量
        :param item_id: 物品id
        :return:
        """
        sql = (f"select * from {self.sql_items_table_name} WHERE need_items_id=? and need_items_price is NOT NULL "
               f"and user_id !={user_id} ORDER BY need_items_price DESC")
        cur = self.conn.cursor()
        cur.execute(sql, (item_id,))
        result = cur.fetchall()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        for row in result:
            want_item = dict(zip(columns, row))

            want_user_id = want_item['user_id']
            want_item_num = want_item['need_items_num']
            want_item_price = want_item['need_items_price']
            get_stone = want_item_price * sell_item_num
            if want_item_num:  # 有数量限制
                if want_item_num < sell_item_num:
                    continue
                return want_item
            else:  # 无数量限制，检查资金是否充足
                want_item_funds = user_store.get_user_funds(want_user_id)  # 获取玩家摊位资金
                if get_stone > want_item_funds:  # 资金不足
                    continue
                return want_item
        return None

    def user_item_want_make(
            self,
            user_id: int,
            need_items_id: int,
            need_items_price: int,
            need_items_num: int,
            need_world: int,
            sell_user: dict):
        """
        插入求购至数据库，数据处理不要放这里
        :param need_world: 求购范围
        :param user_id: 玩家ID
        :param need_items_id: 需求物品id
        :param need_items_price: 期望价格
        :param need_items_num: 需求物品数量
        :param sell_user: 购买者
        :return: None
        """
        now_time = datetime.now()
        now_time_str = str(now_time)
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        item = self.get_want_item(user_id, need_items_id)
        if item:
            # 判断是否存在，存在则update
            sql = (
                f"UPDATE {self.sql_items_table_name} set "
                f"need_items_price=?, "
                f"need_items_num=?,"
                f"need_world=?, "
                f"update_time=?, "
                f"sell_user=? where "
                f"user_id=? and "
                f"need_items_id=?")
            cur.execute(sql, (
                need_items_price,
                need_items_num,
                need_world,
                now_time_str,
                sell_user,
                user_id,
                need_items_id)
                        )
            is_new = False
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO {self.sql_items_table_name} (user_id, need_items_id, need_items_price, need_items_num,
                        need_world, create_time, update_time, sell_user) VALUES (?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (
                user_id,
                need_items_id,
                need_items_price,
                need_items_num,
                need_world,
                now_time_str,
                now_time_str,
                sell_user)
                        )
            is_new = True
        self.conn.commit()
        return is_new
