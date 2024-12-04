from .item_json import items
from .xiuxian2_handle import sql_message, xiuxian_impart, UserBuffDate
import random


def final_user_data(user_data, columns):
    """
    传入用户当前信息、buff信息,返回最终信息
    糟糕的函数
    """
    user_dict = dict(zip((col[0] for col in columns), user_data))

    # 通过字段名称获取相应的值
    impart_data = xiuxian_impart.get_user_info_with_id(user_dict['user_id'])
    if impart_data:
        pass
    else:
        xiuxian_impart._create_user(user_dict['user_id'])
    impart_data = xiuxian_impart.get_user_info_with_id(user_dict['user_id'])
    impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
    impart_mp_per = impart_data['impart_mp_per'] if impart_data is not None else 0
    impart_atk_per = impart_data['impart_atk_per'] if impart_data is not None else 0

    user_buff_data = UserBuffDate(user_dict['user_id']).BuffInfo

    armor_atk_buff = 0
    if int(user_buff_data['armor_buff']) != 0:
        armor_info = items.get_data_by_item_id(user_buff_data['armor_buff'])
        armor_atk_buff = armor_info['atk_buff']

    weapon_atk_buff = 0
    if int(user_buff_data['faqi_buff']) != 0:
        weapon_info = items.get_data_by_item_id(user_buff_data['faqi_buff'])
        weapon_atk_buff = weapon_info['atk_buff']

    main_buff_data = UserBuffDate(user_dict['user_id']).get_user_main_buff_data()
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    main_atk_buff = main_buff_data['atkbuff'] if main_buff_data is not None else 0

    # 改成字段名称来获取相应的值
    user_dict['hp'] = int(user_dict['hp'] * (1 + main_hp_buff + impart_hp_per))
    user_dict['mp'] = int(user_dict['mp'] * (1 + main_mp_buff + impart_mp_per))
    user_dict['atk'] = int((user_dict['atk'] * (user_dict['atkpractice'] * 0.04 + 1) * (1 + main_atk_buff) * (
            1 + weapon_atk_buff) * (1 + armor_atk_buff)) * (1 + impart_atk_per)) + int(user_buff_data['atk_buff'])

    return user_dict


class Increase:
    def __init__(self):
        """
        增益字段 (也可以是减益)
        """
        self.atk = 0
        self.crit = 0
        self.burst = 0
        self.hp_steal = 0
        self.mp_steal = 0


class FightMember:
    def __init__(self, name, hp, hp_max, mp, mp_max, atk, crit, burst, define, main_skill: list, sub_skill: list, team):
        """请使用规范的解包操作进行实例化"""
        self.team = team
        self.name = name
        self.hp = hp
        self.hp_max = hp_max
        self.mp = mp
        self.mp_msx = mp_max
        self.atk = atk
        self.crit = crit
        self.burst = burst
        self.define = define
        self.main_skill = main_skill
        self.sub_skill = sub_skill
        self.buffs = []
        self.increase = Increase()

    def active(self, enemy, msg):
        # buff生效
        for buff in (self.buffs + self.main_skill + self.sub_skill):
            buff.act(self, enemy, msg)
        if self.main_skill:
            for skill in self.main_skill:
                skill.act(self, enemy, msg)
        if self.sub_skill:
            for sub in self.sub_skill:
                sub.act(self, enemy, msg)
        return msg


class PlayerFight:
    def __init__(self, user_fight_info, team):
        self.team = team


def player_fight(user_id_dict, fight_key: int = 0):
    """
    玩家战斗
    :param user_id_dict: 需要进入战斗的玩家id字典{玩家id:玩家阵营}，例{123456:1, 123457:2}
    :param fight_key:战斗类型 0不掉血战斗，切磋，1掉血战斗
    """
    fight_dict = {}  # 初始化战斗字典
    for user_id, team in user_id_dict.items():
        user_fight_info = sql_message.get_user_fight_info(user_id)
        fight_dict[user_id] = PlayerFight(user_fight_info, team)
    winner, fight_msg, after_fight_user_info_list = get_fight(fight_dict)
    if fight_key:
        for user_id, user_after_fight_info in after_fight_user_info_list.items():
            sql_message.update_user_info_by_fight_obj(user_id, user_after_fight_info)
    return winner, fight_msg


def get_fight(pre_fight_dict: dict, max_turn: int = 20):
    """
    进行战斗
    :param pre_fight_dict: 战斗中对象字典
    :param max_turn: 最大战斗回合 0为无限回合
    """
    # 排轴
    fight_dict = dict(sorted(pre_fight_dict.items(), key=lambda x: x[1].speed, reverse=True))
    loser = []
    msg = ""
    winner = None
    while max_turn := max_turn - 1:
        for user_id, fight_player in fight_dict.items():
            if not fight_player.status:
                continue
            msg += f"☆----{fight_player.nane}的回合----☆"
            if fight_player.pass_turn:
                fight_player.pass_turn -= 1
                msg += f"{fight_player.nane}动弹不得！"
                continue
            enemy_list = [user_id for user_id in fight_dict
                          if fight_dict[user_id].team != fight_player.team and fight_dict[user_id].status]
            if not enemy_list:
                msg += f"{fight_player.nane}方胜利！"
                winner = fight_player.team
                break
            enemy_id = random.choice(enemy_list)
            enemy = fight_dict[enemy_id]
            msg= fight_player.active(enemy, msg)
            if kill_user := fight_player.turn_kill:
                loser.append(kill_user)
                fight_dict[kill_user].status = 0
    if not winner:
        msg += "你们打的天昏地暗，被大能叫停！！！"
    # 盘点回合
    return winner, msg, fight_dict
