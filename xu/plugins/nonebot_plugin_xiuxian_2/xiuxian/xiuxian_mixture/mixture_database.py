try:
    import ujson as json
except ImportError:
    import json
import sqlite3
from datetime import datetime
from pathlib import Path
from nonebot.log import logger
from ..xiuxian_config import XiuConfig
from .. import DRIVER
import threading

DATABASE = Path() / "data" / "xiuxian" / "items_database"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class MixtureData:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    # 单例化数据库连接
    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(MixtureData, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "mixture.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "mixture.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            logger.opt(colors=True).info(f"<green>合成表数据库已连接！</green>")
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>合成表数据库关闭！</green>")

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()
        try:
            c.execute(f"select count(1) from mixture_table")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "mixture_table" (
      "item_id" INTEGER NOT NULL,
      "need_items_id" TEXT DEFAULT NULL,
      "need_items_num" TEXT DEFAULT NULL,
      "create_time" TEXT,
      "update_time" TEXT,
      "state" TEXT,
      "is_bind_mixture" integer DEFAULT 0
      );""")

        for i in XiuConfig().sql_mixture:  # 自动补全
            try:
                c.execute(f"select {i} from mixture_table")
            except sqlite3.OperationalError:
                logger.opt(colors=True).info("<yellow>mixture_table有字段不存在，开始创建\r</yellow>")
                sql = f"ALTER TABLE user_xiuxian ADD COLUMN {i} INTEGER DEFAULT 0;"
                logger.opt(colors=True).info(f"<green>{sql}</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        MixtureData().close()
    # 上面是数据库校验，别动

    def get_all_table(self) -> list | None:
        """
        获取所有合成表数据，字典输出
        :return:
        """
        sql = f"SELECT * FROM mixture_table"
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        results = []
        for row in result:
            back_dict = dict(zip(columns, row))
            results.append(back_dict)
        return results

    def get_table_by_item_id(self, item_id):
        """
        获取物品合成表
        :param item_id: 合成物品id
        :return:
        """
        sql = f"select * from mixture_table WHERE item_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, item_id)
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        item_dict = dict(zip(columns, result))
        return item_dict
        pass

    def send_back(self, item_id: int, need_items_id: list, need_items_num: list,
                  state='', is_bind_mixture=0):
        """
        插入配方至合成表
        :param item_id: 合成物品ID
        :param need_items_id: 需求物品id
        :param need_items_num: 需求物品数量
        :param state: 特殊状态传导
        :param is_bind_mixture: 是否合成为绑定物品,0-非绑定,1-绑定
        :return: None
        """
        now_time = datetime.now()
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        table = self.get_table_by_item_id(item_id)
        if table:
            # 判断是否存在，存在则update
            sql = f"""INSERT INTO mixture_table (item_id, need_items_id, need_items_num, update_time, state, is_bind_mixture)
                VALUES (?,?,?,?,?,?)"""
            cur.execute(sql, (item_id, need_items_id, need_items_num, now_time, state, is_bind_mixture))
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO mixture_table (item_id, need_items_id, need_items_num, create_time, update_time, state, is_bind_mixture)
                VALUES (?,?,?,?,?,?,?)"""
            cur.execute(sql, (item_id, need_items_id, need_items_num, now_time, now_time, state, is_bind_mixture))
        self.conn.commit()


@DRIVER.on_shutdown
async def close_db():
    MixtureData().close()