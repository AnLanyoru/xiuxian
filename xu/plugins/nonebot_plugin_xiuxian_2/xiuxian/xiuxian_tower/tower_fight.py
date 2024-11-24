from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_utils.player_fight import Boss_fight
from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_utils.xiuxian2_handle import UserBuffDate, sql_message, \
    xiuxian_impart


async def get_tower_battle_info(user_info, tower_floor_info: dict, bot_id):
    """获取Boss战事件的内容"""
    player = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '防御': 0}
    userinfo = sql_message.get_user_real_info(user_info['user_id'])
    user1_weapon_data = UserBuffDate(user_info['user_id']).get_user_weapon_data()
    user_armor_data = UserBuffDate(user_info['user_id']).get_user_armor_buff_data()  # 秘境战斗防具会心
    user_main_crit_data = UserBuffDate(user_info['user_id']).get_user_main_buff_data()  # 秘境战斗功法会心

    if user_main_crit_data is not None:  # 秘境战斗功法会心
        main_crit_buff = ((user_main_crit_data['crit_buff']) * 100)
    else:
        main_crit_buff = 0

    if user_armor_data is not None:  # 秘境战斗防具会心
        armor_crit_buff = user_armor_data['crit_buff']
    else:
        armor_crit_buff = 0

    if user1_weapon_data is not None:
        player['会心'] = int(((user1_weapon_data['crit_buff']) + armor_crit_buff + main_crit_buff) * 100)
    else:
        player['会心'] = (armor_crit_buff + main_crit_buff) * 100

    user1_impart_data = xiuxian_impart.get_user_info_with_id(user_info['user_id'])

    player['user_id'] = userinfo['user_id']
    player['道号'] = userinfo['user_name']
    player['气血'] = userinfo['hp']
    player['传承气血'] = user1_impart_data['impart_hp_per'] if user1_impart_data else 0
    player['攻击'] = userinfo['atk']
    player['真元'] = userinfo['mp']
    player['传承真元'] = user1_impart_data['impart_mp_per'] if user1_impart_data else 0
    player['exp'] = userinfo['exp']
    player['level'] = userinfo['level']

    boss_info = {
        "name": tower_floor_info["name"],
        "气血": int(tower_floor_info["hp"]),
        "总血量": int(tower_floor_info["hp"]),
        "攻击": int(tower_floor_info["atk"]),
        "真元": int(tower_floor_info["mp"]),
        "jj": "虚劫境",
        'stone': 1
    }

    result, victor, bossinfo_new, stone = await Boss_fight(player, boss_info, bot_id=bot_id)  # 未开启，1不写入，2写入

    return result, victor
