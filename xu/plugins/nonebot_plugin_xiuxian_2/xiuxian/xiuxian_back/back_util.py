import operator
import random

from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_place import place
from ..xiuxian_utils.data_source import jsondata
import json
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.xiuxian2_handle import (
    XIUXIAN_IMPART_BUFF
)

from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, UserBuffDate,
    get_weapon_info_msg, get_armor_info_msg,
    get_player_info, save_player_info,
    get_sec_msg, get_main_info_msg, get_sub_info_msg
)
from datetime import datetime
from pathlib import Path
from ..xiuxian_config import convert_rank, XiuConfig

sql_message = XiuxianDateManage()
xiuxian_impart = XIUXIAN_IMPART_BUFF()

YAOCAIINFOMSG = {
    "-1": "性寒",
    "0": "性平",
    "1": "性热",
    "2": "生息",
    "3": "养气",
    "4": "炼气",
    "5": "聚元",
    "6": "凝神",
}


def check_equipment_can_use(user_id, goods_id):
    """
    装备数据库字段：
        good_type -> '装备'
        state -> 0-未使用， 1-已使用
        goods_num -> '目前数量'
        all_num -> '总数量'
        update_time ->使用的时候更新
        action_time ->使用的时候更新
    判断:
        state = 0, goods_num = 1, all_num =1  可使用
        state = 1, goods_num = 1, all_num =1  已使用
        state = 1, goods_num = 2, all_num =2  已装备，多余的，不可重复使用
    顶用：
    """
    flag = False
    back_equipment = sql_message.get_item_by_good_id_and_user_id(user_id, goods_id)
    if back_equipment['state'] == 0:
        flag = True
    return flag


def get_use_equipment_sql(user_id, goods_id):
    """
    使用装备
    返回sql,和法器或防具
    """
    sql_str = []
    item_info = items.get_data_by_item_id(goods_id)
    user_buff_info = UserBuffDate(user_id).BuffInfo
    now_time = datetime.now()
    item_type = ''
    if item_info['item_type'] == "法器":
        item_type = "法器"
        in_use_id = user_buff_info['faqi_buff']
        sql_str.append(
            f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=1 WHERE user_id={user_id} and goods_id={goods_id}")  # 装备
        if in_use_id != 0:
            sql_str.append(
                f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=0 WHERE user_id={user_id} and goods_id={in_use_id}")  # 取下原有的

    if item_info['item_type'] == "防具":
        item_type = "防具"
        in_use_id = user_buff_info['armor_buff']
        sql_str.append(
            f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=1 WHERE user_id={user_id} and goods_id={goods_id}")  # 装备
        if in_use_id != 0:
            sql_str.append(
                f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=0 WHERE user_id={user_id} and goods_id={in_use_id}")  # 取下原有的

    return sql_str, item_type


def get_no_use_equipment_sql(user_id, goods_id):
    """
    卸载装备
    返回sql,和法器或防具
    """
    item_info = items.get_data_by_item_id(goods_id)
    user_buff_info = UserBuffDate(user_id).BuffInfo
    now_time = datetime.now()
    sql_str = []
    item_type = ""

    # 检查装备类型，并确定要卸载的是哪种buff
    if item_info['item_type'] == "法器":
        item_type = "法器"
        in_use_id = user_buff_info['faqi_buff']
    elif item_info['item_type'] == "防具":
        item_type = "防具"
        in_use_id = user_buff_info['armor_buff']
    else:
        return sql_str, item_type

    # 如果当前装备正被使用，或者存在需要卸载的其他装备
    if goods_id == in_use_id or in_use_id != 0:
        # 卸载当前装备
        sql_str.append(
            f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=0 WHERE user_id={user_id} and goods_id={goods_id}")
        # 如果还有其他装备需要卸载（对于法器和防具的情况）
        if in_use_id != 0 and goods_id != in_use_id:
            sql_str.append(
                f"UPDATE back set update_time='{now_time}',action_time='{now_time}',state=0 WHERE user_id={user_id} and goods_id={in_use_id}")

    return sql_str, item_type


def check_equipment_use_msg(user_id, goods_id):
    """
    检测装备是否已用
    """
    user_back = sql_message.get_item_by_good_id_and_user_id(user_id, goods_id)
    state = user_back['state']
    is_use = False
    if state == 0:
        is_use = False
    if state == 1:
        is_use = True
    return is_use


def get_user_main_back_msg(user_id):
    """
    获取背包内的所有物品信息
    """
    l_equipment_msg = []
    l_skill_msg = []
    l_shenwu_msg = []
    l_xiulianitem_msg = []
    l_libao_msg = []
    l_tdqw_msg = []
    l_tools_msg = []
    l_msg = []
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    if user_backs is None:
        return l_msg
    for user_back in user_backs:
        if user_back['goods_type'] == "装备":
            l_equipment_msg = get_equipment_msg(l_equipment_msg, user_id, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "技能":
            l_skill_msg = get_skill_msg(l_skill_msg, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "神物":
            l_shenwu_msg = get_shenwu_msg(l_shenwu_msg, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "聚灵旗":
            l_xiulianitem_msg = get_jlq_msg(l_xiulianitem_msg, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "礼包":
            l_libao_msg = get_libao_msg(l_libao_msg, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "天地奇物":
            l_tdqw_msg = get_tdqw_msg(l_tdqw_msg, user_back['goods_id'], user_back['goods_num'])

        elif user_back['goods_type'] == "道具":
            l_tools_msg = get_tools_msg(l_tools_msg, user_back['goods_id'], user_back['goods_num'])

    if l_equipment_msg:
        top_msg = "☆------我的装备------☆\r" + l_equipment_msg[0]
        l_msg.append(top_msg)
        for msg in l_equipment_msg[1:]:
            l_msg.append(msg)

    if l_skill_msg:
        top_msg = "☆------拥有技能书------☆\r" + l_skill_msg[0]
        l_msg.append(top_msg)
        for msg in l_skill_msg[1:]:
            l_msg.append(msg)

    if l_shenwu_msg:
        top_msg = "☆------神物------☆\r" + l_shenwu_msg[0]
        l_msg.append(top_msg)
        for msg in l_shenwu_msg[1:]:
            l_msg.append(msg)

    if l_xiulianitem_msg:
        top_msg = "☆------修炼物品------☆\r" + l_xiulianitem_msg[0]
        l_msg.append(top_msg)
        for msg in l_xiulianitem_msg[1:]:
            l_msg.append(msg)

    if l_libao_msg:
        top_msg = "☆------礼包------☆\r" + l_libao_msg[0]
        l_msg.append(top_msg)
        for msg in l_libao_msg[1:]:
            l_msg.append(msg)

    if l_tdqw_msg:
        top_msg = "☆------天地奇物------☆\r" + l_tdqw_msg[0]
        l_msg.append(top_msg)
        for msg in l_tdqw_msg[1:]:
            l_msg.append(msg)

    if l_tools_msg:
        top_msg = "☆------持有道具------☆\r" + l_tools_msg[0]
        l_msg.append(top_msg)
        for msg in l_tools_msg[1:]:
            l_msg.append(msg)

    return l_msg


def get_user_main_back_msg_easy(user_id):
    """
    获取背包内的指定物品信息
    """
    l_msg = []
    item_types = ["装备", "技能", "神物", "聚灵旗", "礼包", "天地奇物", "道具"]
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    if user_backs is None:
        return l_msg
    l_types_dict = {}
    for user_back in user_backs:
        goods_type = user_back.get('goods_type')
        if not l_types_dict.get(goods_type):
            l_types_dict[goods_type] = []
        l_types_dict[goods_type].append(user_back)
    l_types_msg_dict = {}
    for item_type in item_types:
        if l_items := l_types_dict.get(item_type):
            l_items.sort(key=lambda k: int(items.items.get(str(k.get('goods_id')), {}).get('rank')))
            l_items_msg = []
            l_types_sec_dict = {}
            for item in l_items:
                item_info = items.get_data_by_item_id(item['goods_id'])
                item_type_sec = item_info.get('item_type')
                if not l_types_sec_dict.get(item_type_sec):
                    l_types_sec_dict[item_type_sec] = []
                level = f"{item_info.get('level')} - " if item_info.get('level') else ''
                bind_msg = f"(绑定:{item['bind_num']})" if item['bind_num'] else ""
                l_types_sec_dict[item_type_sec].append(f"{level}{item['goods_name']} - "
                                                       f"数量：{item['goods_num']}{bind_msg}")
            for item_type_sec, l_items_sec_msg in l_types_sec_dict.items():
                head_msg = f" ~ {item_type_sec}:\r" if item_type_sec != item_type else ''
                top_msg = head_msg + l_items_sec_msg[0]
                l_items_msg.append(top_msg)
                l_items_msg = operator.add(l_items_msg, l_items_sec_msg[1:])
            l_types_msg_dict[item_type] = l_items_msg
    for item_type, l_items_msg in l_types_msg_dict.items():
        top_msg = f"☆------{item_type}------☆\r" + l_items_msg[0]
        l_msg.append(top_msg)
        l_msg = operator.add(l_msg, l_items_msg[1:])
    return l_msg


def get_user_back_msg(user_id, item_types: list):
    """
    获取背包内的指定物品信息
    """
    l_msg = []
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    if user_backs is None:
        return l_msg
    l_types_dict = {}
    for user_back in user_backs:
        goods_type = user_back.get('goods_type')
        if not l_types_dict.get(goods_type):
            l_types_dict[goods_type] = []
        l_types_dict[goods_type].append(user_back)
    l_types_msg_dict = {}
    for item_type in item_types:
        if l_items := l_types_dict.get(item_type):
            l_items.sort(key=lambda k: int(items.items.get(str(k.get('goods_id')), {}).get('rank')))
            l_items_msg = []
            l_types_sec_dict = {}
            for item in l_items:
                item_info = items.get_data_by_item_id(item['goods_id'])
                item_type_sec = item_info.get('item_type')
                if not l_types_sec_dict.get(item_type_sec):
                    l_types_sec_dict[item_type_sec] = []
                level = f"{item_info.get('level')} - " if item_info.get('level') else ''
                bind_msg = f"(绑定:{item['bind_num']})" if item['bind_num'] else ""
                l_types_sec_dict[item_type_sec].append(f"{level}{item['goods_name']} - "
                                                       f"数量：{item['goods_num']}{bind_msg}")
            for item_type_sec, l_items_sec_msg in l_types_sec_dict.items():
                head_msg = f" ~ {item_type_sec}:\r" if item_type_sec != item_type else ''
                top_msg = head_msg + l_items_sec_msg[0]
                l_items_msg.append(top_msg)
                l_items_msg = operator.add(l_items_msg, l_items_sec_msg[1:])
            l_types_msg_dict[item_type] = l_items_msg
    for item_type, l_items_msg in l_types_msg_dict.items():
        top_msg = f"☆------{item_type}------☆\r" + l_items_msg[0]
        l_msg.append(top_msg)
        l_msg = operator.add(l_msg, l_items_msg[1:])
    return l_msg


def get_user_skill_back_msg(user_id):
    """
    获取背包内的技能信息, 未使用，并入背包
    """
    l_skill_msg = []
    l_msg = [{'type': 'node', 'data': {'name': '技能背包', 'uin': 0, 'content': '道友还未拥有技能书'}}]
    pull_skill = []
    user_backs = sql_message.get_back_skill_msg(user_id, "技能")  # list(back)
    if user_backs is None:
        return l_msg
    for user_back in user_backs:
        if user_back['goods_type'] == "技能":
            l_skill_msg = get_skill_msg(l_skill_msg, user_back['goods_id'], user_back['goods_num'])
    if l_skill_msg:
        pull_skill.append("\r☆------拥有技能书------☆")
        for msg in l_skill_msg:
            pull_skill.append(msg)
    return pull_skill


def get_user_elixir_back_msg(user_id):
    """
    获取背包内的丹药信息
    """
    l_elixir_msg = []
    l_ldl_msg = []
    l_msg = []
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    if user_backs is None:
        return l_msg
    for user_back in user_backs:
        if user_back['goods_type'] == "丹药":
            l_elixir_msg = get_elixir_msg(l_elixir_msg, user_back['goods_id'], user_back['goods_num'])
        elif user_back['goods_type'] == "炼丹炉":
            l_ldl_msg = get_ldl_msg(l_ldl_msg, user_back['goods_id'], user_back['goods_num'])

    if l_ldl_msg:
        l_msg.append("☆------炼丹炉------☆")
    for msg in l_ldl_msg:
        l_msg.append(msg)

    if l_elixir_msg:
        l_msg.append("☆------我的丹药------☆")
        for msg in l_elixir_msg:
            l_msg.append(msg)
    return l_msg


def get_libao_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的礼包信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"拥有数量：{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_tdqw_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的天地奇物信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"介绍：{item_info['desc']}\r"
    msg += f"蕴含天地精华：{item_info['buff']}\r"
    msg += f"拥有数量：{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_tools_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的道具信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"介绍：{item_info['desc']}\r"
    msg += f"拥有数量：{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_user_yaocai_back_msg(user_id):
    """
    获取背包内的药材信息
    """
    l_yaocai_msg = []
    l_msg = []
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    if user_backs is None:
        return l_msg
    level_dict = {"一品药材": 1, "二品药材": 2, "三品药材": 3, "四品药材": 4,
                  "五品药材": 5, "六品药材": 6, "七品药材": 7, "八品药材": 8, "九品药材": 9}
    user_backs.sort(key=lambda k: level_dict.get(items.items.get(str(k.get('goods_id'))).get('level'), 0))
    for user_back in user_backs:
        if user_back['goods_type'] == "药材":
            l_yaocai_msg = get_yaocai_msg(l_yaocai_msg, user_back['goods_id'], user_back['goods_num'])

    if l_yaocai_msg:
        l_msg.append("☆------拥有药材------☆")
        for msg in l_yaocai_msg:
            l_msg.append(msg)
    return l_msg


def get_user_yaocai_back_msg_easy(user_id):
    """
    获取背包内的药材信息
    """
    l_yaocai_msg = []
    l_msg = []
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    level_dict = {"一品药材": 1, "二品药材": 2, "三品药材": 3, "四品药材": 4,
                  "五品药材": 5, "六品药材": 6, "七品药材": 7, "八品药材": 8, "九品药材": 9}
    user_backs.sort(key=lambda k: level_dict.get(
        items.items.get(str(k.get('goods_id'))).get('level'), 0) + 0.01 * len(k.get('goods_name')))
    if user_backs is None:
        return l_msg
    for user_back in user_backs:
        if user_back['goods_type'] == "药材":
            item_info = items.get_data_by_item_id(user_back['goods_id'])
            level = f"{item_info.get('level', '未知品级')[:-2]} - " if item_info.get('level') else ''
            bind_msg = f"(绑定:{user_back['bind_num']})" if user_back['bind_num'] else ""
            l_yaocai_msg.append(f"{level}{user_back['goods_name']} "
                                f"- 数量：{user_back['goods_num']}{bind_msg}")

    if l_yaocai_msg:
        l_msg.append("☆------拥有药材------☆")
        for msg in l_yaocai_msg:
            l_msg.append(msg)
    return l_msg


def get_yaocai_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的药材信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"品级：{item_info['level']}\r"
    msg += get_yaocai_info(item_info)
    msg += f"\r拥有数量:{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_jlq_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的修炼物品信息，聚灵旗
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"效果：{item_info['desc']}"
    msg += f"\r拥有数量:{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_ldl_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的炼丹炉信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"效果：{item_info['desc']}"
    msg += f"\r拥有数量:{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_yaocai_info(yaocai_info):
    """
    获取药材信息
    """
    msg = f"主药 {YAOCAIINFOMSG[str(yaocai_info['主药']['h_a_c']['type'])]}"
    msg += f"{yaocai_info['主药']['h_a_c']['power']}"
    msg += f" {YAOCAIINFOMSG[str(yaocai_info['主药']['type'])]}"
    msg += f"{yaocai_info['主药']['power']}\r"
    msg += f"药引 {YAOCAIINFOMSG[str(yaocai_info['药引']['h_a_c']['type'])]}"
    msg += f"{yaocai_info['药引']['h_a_c']['power']}"
    msg += f"辅药 {YAOCAIINFOMSG[str(yaocai_info['辅药']['type'])]}"
    msg += f"{yaocai_info['辅药']['power']}"

    return msg


def get_equipment_msg(l_msg, user_id, goods_id, goods_num):
    """
    获取背包内的装备信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = ""
    if item_info['item_type'] == '防具':
        msg = get_armor_info_msg(goods_id, item_info)
    elif item_info['item_type'] == '法器':
        msg = get_weapon_info_msg(goods_id, item_info)
    msg += f"\r拥有数量:{goods_num}"
    is_use = check_equipment_use_msg(user_id, goods_id)
    if is_use:
        msg += f"\r已装备"
    else:
        msg += f"\r可装备"
    l_msg.append(msg)
    return l_msg


def get_skill_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的技能信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = ""
    if item_info['item_type'] == '神通':
        msg = f"{item_info['level']}神通-{item_info['name']}:"
        msg += get_sec_msg(item_info)
    elif item_info['item_type'] == '功法':
        msg = f"{item_info['level']}功法-"
        msg += get_main_info_msg(goods_id)[1]
    elif item_info['item_type'] == '辅修功法':  # 辅修功法12
        msg = f"{item_info['level']}辅修功法-"
        msg += get_sub_info_msg(goods_id)[1]
    msg += f"\r拥有数量:{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_elixir_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的丹药信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    msg = f"名字：{item_info['name']}\r"
    msg += f"效果：{item_info['desc']}\r"
    msg += f"拥有数量：{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_shenwu_msg(l_msg, goods_id, goods_num):
    """
    获取背包内的神物信息
    """
    item_info = items.get_data_by_item_id(goods_id)
    try:
        desc = item_info['desc']
    except KeyError:
        desc = "这个东西本来会报错让背包出不来，当你看到你背包有这个这个东西的时候请联系超管解决。"

    msg = f"名字：{item_info['name']}\r"
    msg += f"效果：{desc}\r"
    msg += f"拥有数量：{goods_num}"
    l_msg.append(msg)
    return l_msg


def get_item_msg(goods_id):
    """
    获取单个物品的消息
    """
    item_info = items.get_data_by_item_id(goods_id)
    if item_info['type'] == '丹药':
        msg = f"名字：{item_info['name']}\r"
        msg += f"效果：{item_info['desc']}"

    elif item_info['item_type'] == '神物':
        msg = f"名字：{item_info['name']}\r"
        msg += f"效果：{item_info['desc']}"

    elif item_info['item_type'] == '神通':
        msg = f"名字：{item_info['name']}\r"
        msg += f"品阶：{item_info['level']}\r"
        msg += f"效果：{get_sec_msg(item_info)}"

    elif item_info['item_type'] == '功法':
        msg = f"名字：{item_info['name']}\r"
        msg += f"品阶：{item_info['level']}\r"
        msg += f"效果：{get_main_info_msg(goods_id)[1]}"

    elif item_info['item_type'] == '辅修功法':  # 辅修功法11
        msg = f"名字：{item_info['name']}\r"
        msg += f"品阶：{item_info['level']}\r"
        msg += f"效果：{get_sub_info_msg(goods_id)[1]}"

    elif item_info['item_type'] == '防具':
        msg = get_armor_info_msg(goods_id, item_info)

    elif item_info['item_type'] == '法器':
        msg = get_weapon_info_msg(goods_id, item_info)

    elif item_info['item_type'] == "药材":
        msg = get_yaocai_info_msg(goods_id, item_info)

    elif item_info['item_type'] == "聚灵旗":
        msg = f"名字：{item_info['name']}\r"
        msg += f"效果：{item_info['desc']}"

    elif item_info['item_type'] == "炼丹炉":
        msg = f"名字：{item_info['name']}\r"
        msg += f"介绍：{item_info['desc']}"

    elif item_info['item_type'] == "道具":
        msg = f"名字：{item_info['name']}\r"
        msg += f"介绍：{item_info['desc']}"

    elif item_info['item_type'] == "天地奇物":
        msg = f"名字：{item_info['name']}\r"
        msg += f"介绍：{item_info['desc']}\r"
        msg += f"蕴含天地精华：{item_info['buff']}\r"
        msg += "天地奇物可用于：\r直接使用：使用后获取奇物内蕴含的天地精华，发送天地精华来获得使用帮助\r作为素材：除了直接使用外，天地奇物还可用于锻造增强武器，升级丹炉，制造武器，制作防具等等......"

    else:
        msg = '不支持的物品'
    return msg


def get_item_msg_rank(goods_id):
    """
    获取单个物品的rank
    """
    item_info = items.get_data_by_item_id(goods_id)
    if item_info:
        pass
    else:
        return 520
    if item_info['type'] == '丹药':
        msg = item_info['rank']
    elif item_info['item_type'] == '神通':
        msg = item_info['rank']
    elif item_info['item_type'] == '功法':
        msg = item_info['rank']
    elif item_info['item_type'] == '辅修功法':
        msg = item_info['rank']
    elif item_info['item_type'] == '防具':
        msg = item_info['rank']
    elif item_info['item_type'] == '法器':
        msg = item_info['rank']
    elif item_info['item_type'] == "药材":
        msg = item_info['rank']
    elif item_info['item_type'] == "聚灵旗":
        msg = item_info['rank']
    elif item_info['item_type'] == "炼丹炉":
        msg = item_info['rank']
    else:
        msg = 520
    return int(msg)


def get_yaocai_info_msg(goods_id, item_info):
    msg = f"名字：{item_info['name']}\r"
    msg += f"品级：{item_info['level']}\r"
    msg += get_yaocai_info(item_info)
    return msg


def check_use_elixir(user_id, goods_id, num):
    user_info = sql_message.get_user_info_with_id(user_id)
    user_rank = convert_rank(user_info['level'])[0]
    goods_info = items.get_data_by_item_id(goods_id)
    goods_rank = goods_info['rank']
    goods_name = goods_info['name']
    back = sql_message.get_item_by_good_id_and_user_id(user_id, goods_id)
    goods_all_num = back['all_num']
    if goods_info['buff_type'] == "level_up_rate":  # 增加突破概率的丹药
        if abs(goods_rank - 55) > user_rank:  # 最低使用限制
            msg = f"丹药：{goods_name}的最低使用境界为{goods_info['境界']}，道友不满足使用条件"
        elif user_rank - abs(goods_rank - 55) > 30:  # 最高使用限制
            msg = f"道友当前境界为：{user_info['level']}，丹药：{goods_name}已不能满足道友，请寻找适合道友的丹药吧！"
        else:  # 检查完毕
            sql_message.update_back_j(user_id, goods_id, num, 1)
            sql_message.update_levelrate(user_id, user_info['level_up_rate'] + goods_info['buff'] * num)
            msg = f"道友成功使用丹药：{goods_name}{num}颗，下一次突破的成功概率提高{goods_info['buff'] * num}%!"

    elif goods_info['buff_type'] == "level_up_big":  # 增加大境界突破概率的丹药
        if goods_rank != user_rank:  # 使用限制
            msg = f"丹药：{goods_name}的使用境界为{goods_info['境界']}，道友不满足使用条件！"
        else:
            if goods_all_num >= goods_info['all_num']:
                msg = f"道友使用的丹药：{goods_name}已经达到丹药的耐药性上限！已经无法使用该丹药了！"
            else:  # 检查完毕
                sql_message.update_back_j(user_id, goods_id, num, 1)
                sql_message.update_levelrate(user_id, user_info['level_up_rate'] + goods_info['buff'] * num)
                msg = f"道友成功使用丹药：{goods_name}{num}颗,下一次突破的成功概率提高{goods_info['buff'] * num}%!"

    elif goods_info['buff_type'] == "hp":  # 回复状态的丹药
        if user_info['root'] == "器师":
            user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
            user_buff_data = UserBuffDate(user_id)
            main_buff_data = user_buff_data.get_user_main_buff_data()
            impart_data = xiuxian_impart.get_user_info_with_id(user_id)
            impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
            main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
            user_max_hp = int((user_msg['exp'] / 2) * jsondata.level_data()[user_msg['level']]["HP"])
            user_max_mp = int(user_info['exp'])
            if user_info['hp'] == user_max_hp and user_info['mp'] == user_max_mp:
                msg = f"道友的状态是满的，用不了哦！"
            else:
                buff = goods_info['buff']
                buff = round((0.016 * user_rank + 0.104) * buff, 2)
                recover_hp = int(buff * user_max_hp * num)
                recover_mp = int(buff * user_max_mp * num)
                user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
                user_buff_data = UserBuffDate(user_id)
                main_buff_data = user_buff_data.get_user_main_buff_data()
                impart_data = xiuxian_impart.get_user_info_with_id(user_id)
                impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
                main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
                max_hp = int((user_msg['exp'] / 2) * jsondata.level_data()[user_msg['level']]["HP"])
                if user_info['hp'] + recover_hp > max_hp:
                    new_hp = max_hp  # 超过最大
                else:
                    new_hp = user_info['hp'] + recover_hp
                if user_info['mp'] + recover_mp > user_max_mp:
                    new_mp = user_max_mp
                else:
                    new_mp = user_info['mp'] + recover_mp
                msg = f"道友成功使用丹药：{goods_name}{num}颗，经过境界转化状态恢复了{int(buff * 100 * num)}%!"
                sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
                sql_message.update_user_hp_mp(user_id, new_hp, new_mp)
        else:
            if abs(goods_rank - 55) > user_rank:  # 使用限制
                msg = f"丹药：{goods_name}的使用境界为{goods_info['境界']}以上，道友不满足使用条件！"
            else:

                user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
                user_buff_data = UserBuffDate(user_id)
                main_buff_data = user_buff_data.get_user_main_buff_data()
                impart_data = xiuxian_impart.get_user_info_with_id(user_id)
                impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
                main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
                max_hp = int((user_msg['exp'] / 2) * jsondata.level_data()[user_msg['level']]["HP"])
                user_max_mp = int(user_info['exp'])
                if user_info['hp'] == max_hp and user_info['mp'] == user_max_mp:
                    msg = f"道友的状态是满的，用不了哦！"
                else:
                    buff = goods_info['buff']
                    buff = round((180 - user_rank + abs(goods_rank - 55)) / 180 * buff, 2)
                    recover_hp = int(buff * max_hp * num)
                    recover_mp = int(buff * user_max_mp * num)
                    if user_info['hp'] + recover_hp > max_hp:
                        new_hp = max_hp  # 超过最大
                    else:
                        new_hp = user_info['hp'] + recover_hp
                    if user_info['mp'] + recover_mp > user_max_mp:
                        new_mp = user_max_mp
                    else:
                        new_mp = user_info['mp'] + recover_mp
                    msg = f"道友成功使用丹药：{goods_name}{num}颗，经过境界转化状态恢复了{int(buff * 100 * num)}%!"
                    sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
                    sql_message.update_user_hp_mp(user_id, new_hp, new_mp)

    elif goods_info['buff_type'] == "all":  # 回满状态的丹药
        if user_info['root'] == "器师":

            user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
            user_buff_data = UserBuffDate(user_id)
            main_buff_data = user_buff_data.get_user_main_buff_data()
            impart_data = xiuxian_impart.get_user_info_with_id(user_id)
            impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
            main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
            user_max_hp = int((user_msg['exp'] / 2) * jsondata.level_data()[user_msg['level']]["HP"])

            user_max_mp = int(user_info['exp'])
            if user_info['hp'] == user_max_hp and user_info['mp'] == user_max_mp:
                msg = f"道友的状态是满的，用不了哦！"
            else:
                sql_message.update_back_j(user_id, goods_id, use_key=1)
                sql_message.update_user_hp(user_id)
                msg = f"道友成功使用丹药：{goods_name}1颗,状态已全部恢复!"
        else:
            if abs(goods_rank - 55) > user_rank:  # 使用限制
                msg = f"丹药：{goods_name}的使用境界为{goods_info['境界']}以上，道友不满足使用条件！"
            else:
                user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
                user_buff_data = UserBuffDate(user_id)
                main_buff_data = user_buff_data.get_user_main_buff_data()
                impart_data = xiuxian_impart.get_user_info_with_id(user_id)
                impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
                main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
                user_max_hp = int((user_msg['exp'] / 2) * jsondata.level_data()[user_msg['level']]["HP"])
                user_max_mp = int(user_info['exp'])
                if user_info['hp'] == user_max_hp and user_info['mp'] == user_max_mp:
                    msg = f"道友的状态是满的，用不了哦！"
                else:
                    sql_message.update_back_j(user_id, goods_id, use_key=1)
                    sql_message.update_user_hp(user_id)
                    msg = f"道友成功使用丹药：{goods_name}1颗,状态已全部恢复!"

    elif goods_info['buff_type'] == "atk_buff":  # 永久加攻击buff的丹药
        if user_info['root'] == "器师":
            buff = goods_info['buff'] * num
            sql_message.updata_user_atk_buff(user_id, buff)
            sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
            msg = f"道友成功使用丹药：{goods_name}{num}颗，攻击力永久增加{buff}点！"
        else:
            if abs(goods_rank - 55) > user_rank:  # 使用限制
                msg = f"丹药：{goods_name}的使用境界为{goods_info['境界']}以上，道友不满足使用条件！"
            else:
                buff = goods_info['buff'] * num
                sql_message.updata_user_atk_buff(user_id, buff)
                sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
                msg = f"道友成功使用丹药：{goods_name}{num}颗，攻击力永久增加{buff}点！"

    elif goods_info['buff_type'] == "exp_up":  # 加固定经验值的丹药
        if abs(goods_rank - 55) > user_rank:  # 使用限制
            msg = f"丹药：{goods_name}的使用境界为{goods_info['境界']}以上，道友不满足使用条件！"
        else:
            exp = goods_info['buff'] * num
            user_hp = int(user_info['hp'] + (exp / 2)) * jsondata.level_data()[user_info['level']]["HP"]
            user_mp = int(user_info['mp'] + exp)
            user_atk = int(user_info['atk'] + (exp / 10))
            sql_message.update_exp(user_id, exp)
            sql_message.update_power2(user_id)  # 更新战力
            sql_message.update_user_attribute(user_id, user_hp, user_mp, user_atk)  # 这种事情要放在update_exp方法里
            sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
            msg = f"道友成功使用丹药：{goods_name}{num}颗,修为增加{exp}点！"
    else:
        msg = f"该类型的丹药目前暂时不支持使用！"
    return msg


def get_use_jlq_msg(user_id, goods_id):
    user_info = sql_message.get_user_info_with_id(user_id)
    if user_info['blessed_spot_flag'] == 0:
        msg = f"道友还未拥有洞天福地，无法使用该物品"
    else:
        item_info = items.get_data_by_item_id(goods_id)
        user_buff_data = UserBuffDate(user_id).BuffInfo
        if int(user_buff_data['blessed_spot']) >= item_info['修炼速度']:
            msg = f"该聚灵旗的等级不能满足道友的福地了，使用了也没效果"
        else:
            mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
            mix_elixir_info['药材速度'] = item_info['药材速度']
            save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
            sql_message.update_back_j(user_id, goods_id)
            sql_message.updata_user_blessed_spot(user_id, item_info['修炼速度'])
            msg = f"道友洞天福地的聚灵旗已经替换为：{item_info['name']}"
    return msg


def get_use_tool_msg(user_id, goods_id, use_num) -> (str, bool):
    """
    使用道具
    :param user_id: 用户ID
    :param goods_id: 物品id
    :param use_num: 使用数量
    :return: 使用结果文本，检查bool
    """
    is_pass = False
    item_info = items.get_data_by_item_id(goods_id)
    user_data = sql_message.get_user_info_with_id(user_id)
    if item_info['buff_type'] == 1:  # 体力药品
        stamina_buff = int(item_info['buff']) * use_num
        now_stamina = user_data['user_stamina']
        set_stamina = now_stamina + stamina_buff
        if set_stamina < XiuConfig().max_stamina:
            sql_message.update_user_stamina(user_id, stamina_buff, 1)
            msg = f"使用{item_info['name']}成功，恢复{stamina_buff}点体力！！"
            is_pass = True
        else:
            msg = f"道友当前体力{now_stamina}/{XiuConfig().max_stamina}，{item_info['name']}将为道友恢复{stamina_buff}点体力，超出上限！！！"
        pass
    elif item_info['buff_type'] == 2:
        # 特殊道具
        msg = f"道友成功使用了{item_info['name']}"
        buff_dict = item_info['buff']
        world_change = buff_dict.get('world')
        root_change = buff_dict.get('root_level')
        if world_change is not None:
            place_goal_list = place.get_world_place_list(world_change)
            place_goal = random.choice(place_goal_list)
            place.set_now_place_id(user_id, place_goal)
            place_name = place.get_place_name(place_goal)
            msg += f"\r霎时间天旋地转,回过神来道友竟被{item_info['name']}带到了【{place_name}】!!!"
        if root_change:
            root_type = sql_message.update_root(user_id, 8)  # 更换灵根
            msg += f"\r道友丹田一片翻腾，灵根转化为了{root_type}!!!"
        pass
    else:
        msg = f"{item_info['name']}使用失败！！可能暂未开放使用！！！"
    return msg, is_pass


def get_shop_data(place_id):
    place_id = str(place_id)
    try:
        data = read_shop()
    except:
        data = {}
        print("无法获取到商店文件开始创建")
    try:
        data[place_id]
    except:
        data[place_id] = {}
        print("该地区商店为空，开始创建")
    save_shop(data)
    return data


PATH = Path(__file__).parent
FILEPATH = PATH / 'shop.json'


def read_shop():
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def save_shop(data):
    data = json.dumps(data, ensure_ascii=False, indent=4)
    savemode = "w"
    with open(FILEPATH, mode=savemode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True
