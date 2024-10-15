from math import *

from . import DRIVER
from .xiuxian_utils.database_cur_get import XiuxianDateCur
from .xiuxian_utils.item_json import Items
import os
import random
import sqlite3
from nonebot.log import logger
from datetime import datetime
from pathlib import Path
try:
    import ujson as json
except ImportError:
    import json

WORKDATA = Path() / "data" / "xiuxian" / "work"
PLAYERSDATA = Path() / "data" / "xiuxian" / "players"
DATABASE = Path() / "data" / "xiuxian"
DATABASE_IMPARTBUFF = Path() / "data" / "xiuxian"
SKILLPATHH = DATABASE / "功法"
WEAPONPATH = DATABASE / "装备"
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_num = "123451234"
items = Items()
place_all = {}
place_id_map = {}
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path

PLACEPATH = Path() / "data" / "xiuxian" / "place"


class Move:
    def __init__(self):
        self.start_id = 0
        self.to_id = 0
        self.need_time = 0


def read_place_data():
    FILEPATH = PLACEPATH / "地区.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
        place_data = json.loads(data)
    return place_data


# 施工中
class PlaceSet:
    def __init__(self, num, name, place):
        self.number = num
        self.name = name
        self.place_set = place
        self.place_type = {"number": num, "name": name, "place": place}
        self.place_dict = {num: (name, place)}
        self.place_id_get = {name: num}

    def get_num(self):
        return self.number

    def get_name(self):
        return self.name

    def get_place(self):
        return self.place_set

    def get_place_dict(self):
        return self.place_dict

    def get_place_id_map(self):
        return self.place_id_get


def merge(dict1, dict2):
    return dict2.update(dict1)


@DRIVER.on_startup
async def read_places_():
    global place_all
    global place_id_map
    place_date = read_place_data()
    for place_id in place_date:
        name = place_date[place_id]["name"]
        x = place_date[place_id]["x"]
        y = place_date[place_id]["y"]
        world = place_date[place_id]["world"]
        merge(PlaceSet(int(place_id), name, (x, y, world)).get_place_dict(), place_all)
        merge(PlaceSet(int(place_id), name, (x, y, world)).get_place_id_map(), place_id_map)
    logger.opt(colors=True).info(f"<green>地区数据读取成功</green>")
# 创建位置对象


class Place:
    def __init__(self):
        self.distance = 0
        self.conn = XiuxianDateCur().conn
        self.place_all = place_all
        self.place_id_map = place_id_map
        self.worlds = {}
        self.world_names = ["凡界", "灵界", "仙界", "无尽神域", "万界洞天中枢"]

    def get_place_dict(self):
        return self.place_all

    def get_worlds(self):
        """获取位面字典"""
        for num in range(len(self.world_names)):
            self.worlds[num] = self.world_names[num]
        return self.worlds

    def get_world_name(self, place_id):
        """
        通过地区ID获取位面名称
        :param place_id: type = int
        :return: type = str
        """
        place_dict = self.get_place_dict()
        world_id = place_dict[place_id][1][2]
        world_name = self.world_names
        return world_name[world_id]

    def get_world_id_name(self, world_id):
        """
        通过位面ID获取位面名称
        :param world_id: type = int
        :return: type = str
        """
        world_name = self.world_names
        return world_name[world_id]

    def get_world_id(self, place_id):
        """
        通过位置ID获取位面ID
        :param place_id: type = int
        :return: type = str
        """
        place_dict = self.get_place_dict()
        world_id = place_dict[place_id][1][2]
        return world_id

    def get_distance(self, place_start, place_to):
        """
        计算两地距离，在洞天中默认为（0，0）坐标
        :param place_start: type = int 起始地点 ID
        :param place_to: type = int 目的地 ID
        :return: type = float|str  若可到达，返回距离，出发点，目的地，不可到达，返回字符串“unachievable”
        """
        place_start = int(place_start)
        place_to = int(place_to)
        set_start = self.get_place_dict()[place_start][1]
        set_to = self.get_place_dict()[place_to][1]
        place_name_1 = self.get_place_dict()[place_start][0]
        place_name_2 = self.get_place_dict()[place_to][0]
        x1 = set_start[0]
        x2 = set_to[0]
        y1 = set_start[1]
        y2 = set_to[1]
        self.distance = sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))
        if set_start[2] != -1 and set_start[2] != set_to[2]:
            return "unachievable", place_name_1, place_name_2
        else:
            return [self.distance, place_name_1, place_name_2]

    def get_place_name(self, place_id):
        """
        通过地点ID获取地点名称
        :param place_id: type = int 地点ID
        :return: type = str 地点名称
        """
        place_dict = self.get_place_dict()
        return place_dict[int(place_id)][0]

    def get_place_id(self, place_name) -> int | None:
        """
        通过地点名称获取地点ID
        :param place_name: type = str 地点名称
        :return: type = int 地点id
        """
        try:
            place_id = self.place_id_map[place_name]
            return place_id
        except KeyError:
            return None

    def get_world_place_list(self, world_id):
        """
        通过位面id获取位面内所有
        :param world_id: 位面id
        :return: 区域id列表
        """
        place_list = []
        for place, place_set in self.place_all.items():
            if place_set[1][2] == world_id:
                place_list.append(place)
            else:
                pass
        return place_list

    def get_user_cd(self, user_id):
        """
        获取用户操作CD
        :param user_id: QQ
        :return: 用户CD信息的字典
        """
        sql = f"SELECT * FROM user_cd  WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if result:
            columns = [column[0] for column in cur.description]
            user_cd_dict = dict(zip(columns, result))
            return user_cd_dict
        else:
            self.insert_user_cd(user_id)
            return None

    def insert_user_cd(self, user_id) -> None:
        """
        添加用户至CD表
        :param user_id: qq
        :return:
        """
        sql = f"INSERT INTO user_cd (user_id) VALUES (?)"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def get_now_place_id(self, user_id):
        """
        通过用户ID获取用户当前位置
        :param user_id: type = str 用户id
        :return: type = int 位置ID
        """
        user_cd_message = self.get_user_cd(user_id)
        user_place_id = user_cd_message["place_id"]
        return user_place_id

    def set_now_place_id(self, user_id, place_id):
        """
        更新用户位置
        :param user_id: 用户ID
        :param place_id:
        :return:
        """
        sql = "UPDATE user_cd SET place_id=? WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (place_id, user_id))
        self.conn.commit()
        pass

    def is_the_same_world(self, player_1, player_2) -> bool:
        """
        判断两位玩家是否在同一位面
        :param player_1: 玩家1 ID
        :param player_2: 玩家2 ID
        :return: 布尔值
        """
        player_1_place = self.get_now_place_id(player_1)
        player_2_place = self.get_now_place_id(player_2)
        player_1_world = self.get_world_id(player_1_place)
        player_2_world = self.get_world_id(player_2_place)
        if player_1_world == player_2_world:
            return True
        else:
            return False

    def is_the_same_place(self, player_1, player_2) -> bool:
        """
        判断两位玩家是否在同一位置
        :param player_1: 玩家1 ID
        :param player_2: 玩家2 ID
        :return: 布尔值
        """
        player_1_place = self.get_now_place_id(player_1)
        player_2_place = self.get_now_place_id(player_2)
        if player_1_place == player_2_place:
            return True
        else:
            return False
