import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from nonebot.log import logger
from .. import DRIVER
import threading

from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import number_to_msg
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.xiuxian2_handle import sql_message

DATABASE = Path() / "data" / "xiuxian" / "players_database"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class WorldTowerData:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    # 单例化数据库连接
    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(WorldTowerData, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        self.sql_user_table_name = "user_tower_info"
        self.sql_tower_info_table_name = "world_tower"
        self.sql_col = ["user_id", "now_floor", "best_floor", "tower_point", "tower_place",
                        "fight_log"]
        self.blob_data_list = ["sell_user"]
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "modus.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "modus.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            logger.opt(colors=True).info(f"<green>额外玩法数据库已连接！</green>")
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>额外玩法数据库关闭！</green>")

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()
        try:
            c.execute(f"select count(1) from {self.sql_tower_info_table_name}")
        except sqlite3.OperationalError:
            c.execute(f"""CREATE TABLE "{self.sql_tower_info_table_name}" (
      "floor" INTEGER NOT NULL,
      "place_id" INTEGER DEFAULT 0,
      "name" TEXT,
      "hp" INTEGER DEFAULT 0,
      "mp" INTEGER DEFAULT 0,
      "atk" INTEGER DEFAULT 0,
      "defence" INTEGER DEFAULT 0
      );""")
        try:
            c.execute(f"select count(1) from {self.sql_user_table_name}")
        except sqlite3.OperationalError:
            c.execute(f"""CREATE TABLE "{self.sql_user_table_name}" (
      "user_id" INTEGER NOT NULL,
      "now_floor" INTEGER DEFAULT 0,
      "best_floor" INTEGER DEFAULT 0,
      "tower_point" INTEGER DEFAULT 0,
      "tower_place" INTEGER DEFAULT 0,
      "fight_log" BLOB
      );""")

        for i in self.sql_col:  # 自动补全
            try:
                c.execute(f"select {i} from {self.sql_user_table_name}")
            except sqlite3.OperationalError:
                logger.opt(colors=True).info(f"<yellow>{self.sql_user_table_name}，开始创建\n</yellow>")
                sql = f"ALTER TABLE {self.sql_user_table_name} ADD COLUMN {i} INTEGER DEFAULT 0;"
                logger.opt(colors=True).info(f"<green>{sql}</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        WorldTowerData().close()

    # 上面是数据库校验，别动

    def get_tower_floor_info(self, floor, place_id) -> dict | None:
        """
        获取指定层数战斗塔信息
        :return:
        """
        sql = f"SELECT * FROM {self.sql_tower_info_table_name} WHERE floor=? and place_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (floor, place_id))

        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        user_store_dict = dict(zip(columns, result))
        return user_store_dict

    def tower_floor_make(
            self,
            floor: int,
            place_id: int,
            name: str,
            hp: int,
            mp: int,
            atk: int,
            defence: float):
        """
        插入塔楼层信息至数据库，数据处理不要放这里
        """
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        item = self.get_tower_floor_info(floor, place_id)
        if item:
            # 判断是否存在，存在则update
            sql = (f"UPDATE {self.sql_tower_info_table_name} "
                   f"set name=?, hp=?, mp=?, atk=?, defence=? "
                   f"where floor=? and place_id=?")
            cur.execute(sql, (name, hp, mp, atk, defence, floor, place_id))
            is_new = False
        else:
            # 判断是否存在，不存在则INSERT
            sql = (f"INSERT INTO {self.sql_tower_info_table_name} "
                   f"(floor, place_id, name, hp, mp, atk, defence) "
                   f"VALUES (?,?,?,?,?,?,?)")
            cur.execute(sql, (floor, place_id, name, hp, mp, atk, defence))
            is_new = True
        self.conn.commit()
        return is_new

    def get_user_tower_info(self, user_id):
        """
        获取指定用户的塔信息
        :param user_id: 用户id
        :return:
        """
        sql = f"select * from {self.sql_user_table_name} WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id, ))
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        user_dict = dict(zip(columns, result))
        return user_dict

    def user_tower_info_make(
            self,
            user_id: int,
            now_floor: int,
            best_floor: int,
            tower_point: int,
            tower_place: int,
            fight_log: dict):
        """

        :param user_id:
        :param now_floor:
        :param best_floor:
        :param tower_point:
        :param tower_place:
        :param fight_log:
        :return:
        """
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        item = self.get_user_tower_info(user_id)
        if item:
            # 判断是否存在，存在则update
            sql = (
                f"UPDATE {self.sql_user_table_name} set "
                f"now_floor=?, "
                f"best_floor=?, "
                f"tower_point=?,"
                f"tower_place=?, "
                f"fight_log=? where "
                f"user_id=?")
            cur.execute(sql, (
                now_floor,
                best_floor,
                tower_point,
                tower_place,
                fight_log,
                user_id)
                        )
            is_new = False
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO {self.sql_user_table_name} (user_id, now_floor, best_floor, 
            tower_point, tower_place, fight_log) VALUES (?,?,?,?,?,?)"""
            cur.execute(sql, (
                user_id,
                now_floor,
                best_floor,
                tower_point,
                tower_place,
                fight_log)
                        )
            is_new = True
        self.conn.commit()
        return is_new


class TowerHandle(WorldTowerData):
    def create_enemy(self):
        input_pass = False
        while not input_pass:
            try:
                place_id = int(input("请输入boss所在通天塔id（所在地图id）"))
                input_pass = True
            except ValueError:
                print("请输入正确的地图id数字")
        input_pass = False
        while not input_pass:
            try:
                floor = int(input("请输入boss所在楼层"))
                input_pass = True
            except ValueError:
                print("请输入正确的楼层数字")


tower_handle = TowerHandle()

if __name__ == '__main__':
    tower_handle.create_enemy()
