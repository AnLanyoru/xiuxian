import random
import re
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.log import logger
from datetime import datetime
from nonebot import on_command, on_fullmatch, require
from nonebot.permission import SUPERUSER

from .limit import CheckLimit, reset_send_stone, reset_stone_exp_up
from .. import DRIVER
from ..xiuxian_exp_up.exp_up_def import exp_up_by_time
from ..xiuxian_impart_pk import impart_pk_check
from ..xiuxian_limit.limit_database import limit_handle
from ..xiuxian_limit.limit_util import LimitCheck
from ..xiuxian_place import place
from ..xiuxian_utils.clean_utils import get_datetime_from_str, date_sub
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, OtherSet, get_player_info,
    save_player_info, UserBuffDate, get_main_info_msg,
    get_user_buff, get_sec_msg, get_sub_info_msg,
    XIUXIAN_IMPART_BUFF
)
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.data_source import jsondata
from nonebot.params import CommandArg
from ..xiuxian_utils.player_fight import Player_fight
from ..xiuxian_utils.utils import (
    number_to, check_user, send_msg_handler,
    check_user_type, get_msg_pic, CommandObjectID, get_id_from_str
)
from ..xiuxian_utils.lay_out import Cooldown
from .two_exp_cd import two_exp_cd

cache_help = {}
sql_message = XiuxianDateManage()  # sql类
xiuxian_impart = XIUXIAN_IMPART_BUFF()
BLESSEDSPOTCOST = 3500000
two_exp_limit = XiuConfig().two_exp_limit  # 默认双修次数上限，修仙之人一天7次也不奇怪（

two_exp_cd_up = require("nonebot_plugin_apscheduler").scheduler

buffinfo = on_fullmatch("我的功法", priority=1, permission=GROUP, block=True)
out_closing = on_command("出关", aliases={"灵石出关"}, priority=5, permission=GROUP, block=True)
in_closing = on_fullmatch("闭关", priority=5, permission=GROUP, block=True)
stone_exp = on_command("灵石修仙", aliases={"灵石修炼", "/灵石修炼"}, priority=1, permission=GROUP, block=True)
two_exp = on_command("双修", priority=5, permission=GROUP, block=True)
mind_state = on_command("我的状态", aliases={"/我的状态"}, priority=1, permission=GROUP, block=True)
select_state = on_command("查看状态", aliases={"查状态"}, priority=1, permission=GROUP, block=True)
qc = on_command("切磋", priority=6, permission=GROUP, block=True)
blessed_spot_create = on_command("洞天福地购买", aliases={"获取洞天福地", "购买洞天福地"}, priority=1, permission=GROUP, block=True)
blessed_spot_info = on_command("洞天福地查看", aliases={"我的洞天福地", "查看洞天福地"}, priority=1, permission=GROUP, block=True)
blessed_spot_rename = on_command("洞天福地改名", aliases={"改名洞天福地", "改洞天福地名"}, priority=1, permission=GROUP, block=True)
ling_tian_up = on_fullmatch("灵田开垦", priority=5, permission=GROUP, block=True)
del_exp_decimal = on_fullmatch("抑制黑暗动乱", priority=9, permission=GROUP, block=True)
my_exp_num = on_fullmatch("我的双修次数", priority=9, permission=GROUP, block=True)
a_test = on_fullmatch("测试保存", priority=9, permission=SUPERUSER, block=True)


# 每日0点重置用户双修次数
@two_exp_cd_up.scheduled_job("cron", hour=0, minute=0)
async def two_exp_cd_up_():

    two_exp_cd.re_data()
    reset_send_stone()
    reset_stone_exp_up()
    logger.opt(colors=True).info(f"<green>日常限制已刷新！</green>")


@blessed_spot_create.handle(parameterless=[Cooldown(at_sender=False)])
async def blessed_spot_creat_(bot: Bot, event: GroupMessageEvent):
    """洞天福地购买"""
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) != 0:
        msg = f"道友已经拥有洞天福地了，请发送洞天福地查看吧~"
        await bot.send(event=event, message=msg)
        await blessed_spot_create.finish()
    if user_info['stone'] < BLESSEDSPOTCOST:
        msg = f"道友的灵石不足{BLESSEDSPOTCOST}枚，无法购买洞天福地"
        await bot.send(event=event, message=msg)
        await blessed_spot_create.finish()
    else:
        sql_message.update_ls(user_id, BLESSEDSPOTCOST, 2)
        sql_message.update_user_blessed_spot_flag(user_id)
        mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
        mix_elixir_info['收取时间'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
        msg = f"恭喜道友拥有了自己的洞天福地，请收集聚灵旗来提升洞天福地的等级吧~\n"
        msg += f"默认名称为：{user_info['user_name']}道友的家"
        sql_message.update_user_blessed_spot_name(user_id, f"{user_info['user_name']}道友的家")
        await bot.send(event=event, message=msg)
        await blessed_spot_create.finish()


@blessed_spot_info.handle(parameterless=[Cooldown(at_sender=False)])
async def blessed_spot_info_(bot: Bot, event: GroupMessageEvent):
    """洞天福地信息"""
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买来购买吧~"
        await bot.send(event=event, message=msg)
        await blessed_spot_info.finish()
    msg = f"\n道友的洞天福地:\n"
    user_buff_data = UserBuffDate(user_id).BuffInfo
    if user_info['blessed_spot_name'] == 0:
        blessed_spot_name = "尚未命名"
    else:
        blessed_spot_name = user_info['blessed_spot_name']
    mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
    msg += f"名字：{blessed_spot_name}\n"
    msg += f"修炼速度：增加{int(user_buff_data['blessed_spot']) * 100}%\n"
    msg += f"灵田数量：{mix_elixir_info['灵田数量']}"
    await bot.send(event=event, message=msg)
    await blessed_spot_info.finish()


@ling_tian_up.handle(parameterless=[Cooldown(at_sender=False)])
async def ling_tian_up_(bot: Bot, event: GroupMessageEvent):
    """洞天福地灵田升级"""
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买吧~"
        await bot.send(event=event, message=msg)
        await ling_tian_up.finish()
    LINGTIANCONFIG = {
        "1": {
            "level_up_cost": 3500000
        },
        "2": {
            "level_up_cost": 5000000
        },
        "3": {
            "level_up_cost": 7000000
        },
        "4": {
            "level_up_cost": 10000000
        },
        "5": {
            "level_up_cost": 15000000
        },
        "6": {
            "level_up_cost": 30000000
        },
        "7": {
            "level_up_cost": 90000000
        },
        "8": {
            "level_up_cost": 150000000
        },
        "9": {
            "level_up_cost": 300000000
        },
        "10": {
            "level_up_cost": 600000000
        },
        "11": {
            "level_up_cost": 1000000000
        },
        "12": {
            "level_up_cost": 2000000000
        },
        "13": {
            "level_up_cost": 3000000000
        },
        "14": {
            "level_up_cost": 4000000000
        }
    }
    mix_elixir_info = get_player_info(user_id, "mix_elixir_info")
    now_num = mix_elixir_info['灵田数量']
    if now_num == len(LINGTIANCONFIG) + 1:
        msg = f"道友的灵田已全部开垦完毕，无法继续开垦了！"
    else:
        cost = LINGTIANCONFIG[str(now_num)]['level_up_cost']
        if int(user_info['stone']) < cost:
            msg = f"本次开垦需要灵石：{cost}，道友的灵石不足！"
        else:
            msg = f"道友成功消耗灵石：{cost}，灵田数量+1,目前数量:{now_num + 1}"
            mix_elixir_info['灵田数量'] = now_num + 1
            save_player_info(user_id, mix_elixir_info, 'mix_elixir_info')
            sql_message.update_ls(user_id, cost, 2)
    await bot.send(event=event, message=msg)
    await ling_tian_up.finish()


@blessed_spot_rename.handle(parameterless=[Cooldown(at_sender=False)])
async def blessed_spot_rename_(bot: Bot, event: GroupMessageEvent):
    """洞天福地改名"""
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    if int(user_info['blessed_spot_flag']) == 0:
        msg = f"道友还没有洞天福地呢，请发送洞天福地购买吧~"
        await bot.send(event=event, message=msg)
        await blessed_spot_rename.finish()
    blessed_spot_name_list = ("霍桐山洞，东岳泰山洞，南岳衡山洞，西岳华山洞，北岳常山洞，中岳嵩山洞，峨嵋山洞，庐山洞，四明山洞，会稽山洞，"
                              "太白山洞，西山洞，小沩山洞，火氓山洞，鬼谷山洞，武夷山洞，玉笥山洞，华盖山洞，盖竹山洞，都峤山洞，白石山洞，"
                              "岣嵝山洞，九嶷山洞，洞阳山洞，幕阜山洞，大酉山洞，金庭山洞，麻 姑山洞，仙都山洞，青田山洞，钟山洞，良常山洞，"
                              "紫山洞，天目山洞，桃源山洞，金华山洞，地肺山，盖竹山，仙磕山，东仙源，西仙源，南田山，玉溜山，清屿山，郁木洞，"
                              "丹霞洞，君山，大若岩，焦源，灵墟，沃洲，天姥岭，若耶溪，金庭山，清远山，安山，马岭山，鹅羊山，洞真墟，青玉坛，"
                              "光天坛，洞灵源，洞宫山，陶山，三皇井 ，烂柯山，勒溪，龙虎山，灵山，泉源，金精山，阁皂山，始丰山，逍遥山，东白源，"
                              "钵池山，论山，毛公坛，鸡笼山，桐柏山，平都山，绿萝山，虎溪山，彰龙山，抱福山，大面山，元晨山，马蹄山，德山，高溪山，"
                              "蓝水，玉峰，天柱山，商谷山，张公洞，司马悔山，长在山，中条山，茭湖鱼澄洞，绵竹山，泸水，甘山，莫寻山，金城山，云山，"
                              "北邙山，卢山，东海山").split("，")
    arg = random.choice(blessed_spot_name_list)
    msg = f"道友的洞天福地成功改名为：{arg}"
    sql_message.update_user_blessed_spot_name(user_id, arg)
    await bot.send(event=event, message=msg)
    await blessed_spot_rename.finish()


@qc.handle(parameterless=[Cooldown(cd_time=10, stamina_cost=0, at_sender=False)])
async def qc_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """切磋，不会掉血"""
    args = args.extract_plain_text()
    give_qq = get_id_from_str(args)  # 使用道号获取用户id，代替原at

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']

    user1 = sql_message.get_user_real_info(user_id)
    user2 = sql_message.get_user_real_info(give_qq)
    if give_qq:
        if give_qq == user_id:
            msg = "道友不会左右互搏之术！"
            await bot.send(event=event, message=msg)
            await qc.finish()

    if user1 and user2:
        player1 = {"user_id": None, "道号": None, "气血": None,
                   "攻击": None, "真元": None, '会心': None, '防御': 0, 'exp': 0}
        player2 = {"user_id": None, "道号": None, "气血": None,
                   "攻击": None, "真元": None, '会心': None, '防御': 0, 'exp': 0}
        # 获取传承buff
        user1_impart_data = xiuxian_impart.get_user_info_with_id(user_id)
        user2_impart_data = xiuxian_impart.get_user_info_with_id(give_qq)

        player1['user_id'] = user1['user_id']
        player1['道号'] = user1['user_name']
        player1['气血'] = user1['hp']
        player1['传承气血'] = user1_impart_data['impart_hp_per'] if user1_impart_data else 0
        player1['攻击'] = user1['atk']
        player1['真元'] = user1['mp']
        player1['传承真元'] = user1_impart_data['impart_mp_per'] if user1_impart_data else 0
        player1['exp'] = user1['exp']
        player1['level'] = user1['level']

        player2['user_id'] = user2['user_id']
        player2['道号'] = user2['user_name']
        player2['气血'] = user2['hp']
        player2['传承气血'] = user2_impart_data['impart_hp_per'] if user2_impart_data else 0
        player2['攻击'] = user2['atk']
        player2['真元'] = user2['mp']
        player2['传承真元'] = user2_impart_data['impart_mp_per'] if user2_impart_data else 0
        player2['exp'] = user2['exp']
        player2['level'] = user2['level']

        result, victor = Player_fight(player1, player2, 1, bot.self_id)
        fight_len = len(result)
        result = result[-9:]
        await send_msg_handler(bot, event, result)
        msg = f"获胜的是{victor}"
        await bot.send(event=event, message=msg)
        await qc.finish()
    else:
        msg = "修仙界没有对方的信息，快邀请对方加入修仙界吧！"
        await bot.send(event=event, message=msg)
        await qc.finish()


@two_exp.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def two_exp_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """双修"""

    _, user_1, _ = check_user(event)

    args = args.extract_plain_text()

    user_1_id = user_1['user_id']
    user_2_id = get_id_from_str(args)  # 使用道号获取用户id，代替原at

    user_2 = sql_message.get_user_info_with_id(user_2_id)

    if user_1 and user_2:
        if user_2_id is None:
            msg = "请输入你道侣的道号,与其一起双修！"
            await bot.send(event=event, message=msg)
            await two_exp.finish()

        if int(user_1_id) == int(user_2_id):
            msg = "道友无法与自己双修！"
            await bot.send(event=event, message=msg)
            await two_exp.finish()
        if user_2:
            exp_1 = user_1['exp']
            exp_2 = user_2['exp']
            if exp_2 > exp_1:
                msg = "修仙大能看了看你，不屑一顾，扬长而去！"
                await bot.send(event=event, message=msg)
                await two_exp.finish()
            else:
                if place.is_the_same_place(int(user_1_id), int(user_2_id)) is False:
                    msg = "道友与你的道侣不在同一位置，请邀约道侣前来双修！！！"
                    await bot.send(event=event, message=msg)
                    await two_exp.finish()
                is_type, msg = check_user_type(user_2_id, 0)
                if is_type:
                    pass
                else:
                    msg = "对方" + msg[2:]
                    await bot.send(event=event, message=msg)
                    await two_exp.finish()
                is_pass, msg = LimitCheck().two_exp_limit_check(user_id_1=user_1_id, user_id_2=user_2_id)
                if not is_pass:
                    await bot.send(event=event, message=msg)
                    await two_exp.finish()
                max_exp_1 = (
                        int(OtherSet().set_closing_type(user_1['level'])) * XiuConfig().closing_exp_upper_limit
                )  # 获取下个境界需要的修为 * 1.5为闭关上限
                max_exp_2 = (
                        int(OtherSet().set_closing_type(user_2['level'])) * XiuConfig().closing_exp_upper_limit
                )
                user_get_exp_max_1 = int(max_exp_1) - user_1['exp']
                user_get_exp_max_2 = int(max_exp_2) - user_2['exp']

                if user_get_exp_max_1 < 0:
                    user_get_exp_max_1 = 0
                if user_get_exp_max_2 < 0:
                    user_get_exp_max_2 = 0

                msg = ""
                msg += f"{user_1['user_name']}与{user_2['user_name']}情投意合，于某地一起修炼了一晚。"
                exp = int((exp_1 + exp_2) * 0.0055)
                max_exp = XiuConfig().two_exp  # 双修上限罪魁祸首
                # 玩家1修为增加
                if exp >= max_exp:
                    exp_limit_1 = max_exp
                else:
                    exp_limit_1 = exp
                if exp_limit_1 >= user_get_exp_max_1:
                    sql_message.update_exp(user_1_id, user_get_exp_max_1)
                    msg += f"{user_1['user_name']}修为到达上限，增加修为{user_get_exp_max_1}。"
                else:
                    sql_message.update_exp(user_1_id, exp_limit_1)
                    msg += f"{user_1['user_name']}增加修为{exp_limit_1}。"
                sql_message.update_power2(user_1_id)
                # 玩家2修为增加
                if exp >= max_exp:
                    exp_limit_2 = max_exp
                else:
                    exp_limit_2 = exp
                if exp_limit_2 >= user_get_exp_max_2:
                    sql_message.update_exp(user_2_id, user_get_exp_max_2)
                    msg += f"{user_2['user_name']}修为到达上限，增加修为{user_get_exp_max_2}。"
                else:
                    sql_message.update_exp(user_2_id, exp_limit_2)
                    msg += f"{user_2['user_name']}增加修为{exp_limit_2}。"
                # 双修彩蛋，突破概率增加
                if random.randint(1, 100) in [13, 14, 52, 10, 66]:
                    sql_message.update_levelrate(user_1_id, user_1['level_up_rate'] + 2)
                    sql_message.update_levelrate(user_2_id, user_2['level_up_rate'] + 2)
                    msg += f"离开时双方互相留法宝为对方护道,双方各增加突破概率2%。"
                sql_message.update_power2(user_2_id)
                limit_handle.update_user_log_data(user_1_id, msg)
                limit_handle.update_user_log_data(user_2_id, msg)
                await bot.send(event=event, message=msg)
                await two_exp.finish()
    else:
        msg = "修仙者应一心向道，务要留恋凡人！"
        await bot.send(event=event, message=msg)
        await two_exp.finish()


@stone_exp.handle(parameterless=[Cooldown(at_sender=False)])
async def stone_exp_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """灵石修炼"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    user_mes = sql_message.get_user_info_with_id(user_id)  # 获取用户信息
    level = user_mes['level']
    use_exp = user_mes['exp']
    use_stone = user_mes['stone']
    max_exp = (
            int(OtherSet().set_closing_type(level)) * XiuConfig().closing_exp_upper_limit
    )  # 获取下个境界需要的修为 * 1.5为闭关上限
    user_get_exp_max = int(max_exp) - use_exp

    if user_get_exp_max < 0:
        # 校验当当前修为超出上限的问题，不可为负数
        user_get_exp_max = 0

    msg = args.extract_plain_text().strip()
    stone_num = re.findall(r"\d+", msg)  # 灵石数

    if stone_num:
        pass
    else:
        msg = "请输入正确的灵石数量！"
        await bot.send(event=event, message=msg)
        await stone_exp.finish()

    stone_num = int(stone_num[0])

    if use_stone <= stone_num:
        msg = "你的灵石还不够呢，快去赚点灵石吧！"
        await bot.send(event=event, message=msg)
        await stone_exp.finish()

    exp = int(stone_num / 10)
    if exp >= user_get_exp_max:
        # 用户获取的修为到达上限
        stone_num = user_get_exp_max * 10
        exp = int(stone_num / 10)
        num, msg, is_pass = CheckLimit().stone_exp_up_check(user_id, stone_num)
        if is_pass:
            sql_message.update_exp(user_id, exp)
            sql_message.update_power2(user_id)  # 更新战力
            msg = (f"修炼结束，本次修炼到达上限，共增加修为：{number_to(exp)}|{exp},"
                   f"消耗灵石：{number_to(stone_num)}|{stone_num}") + msg
            sql_message.update_ls(user_id, int(stone_num), 2)
            await bot.send(event=event, message=msg)
            await stone_exp.finish()
        else:
            await bot.send(event=event, message=msg)
            await stone_exp.finish()
    else:
        num, msg, is_pass = CheckLimit().stone_exp_up_check(user_id, stone_num)
        if is_pass:
            sql_message.update_exp(user_id, exp)
            sql_message.update_power2(user_id)  # 更新战力
            msg = (f"修炼结束，本次修炼共增加修为：{number_to(exp)}|{exp},"
                   f"消耗灵石：{number_to(stone_num)}|{stone_num}") + msg
            sql_message.update_ls(user_id, int(stone_num), 2)
            await bot.send(event=event, message=msg)
            await stone_exp.finish()
        else:
            await bot.send(event=event, message=msg)
            await stone_exp.finish()


@in_closing.handle(parameterless=[Cooldown(at_sender=False)])
async def in_closing_(bot: Bot, event: GroupMessageEvent):
    """闭关"""
    user_type = 1  # 状态1为闭关状态

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)
    if is_type:  # 符合
        sql_message.in_closing(user_id, user_type)
        msg = "进入闭关状态，如需出关，发送【出关】！"
    await bot.send(event=event, message=msg)
    await in_closing.finish()


@out_closing.handle(parameterless=[Cooldown(at_sender=False)])
async def out_closing_(bot: Bot, event: GroupMessageEvent):
    """出关"""
    # 状态变更事件标识
    user_type = 0  # 状态0为无事件
    # 获取用户信息
    _, user_info, _ = check_user(event)
    # 获取用户id
    user_id = user_info['user_id']

    now_time = datetime.now()
    is_type, msg = check_user_type(user_id, 1)
    if is_type:
        # 进入闭关的时间
        user_cd_message = sql_message.get_user_cd(user_id)
        in_closing_time = get_datetime_from_str(user_cd_message['create_time'])

        # 闭关时长计算(分钟) = second // 60
        time_diff = date_sub(now_time, in_closing_time)
        exp_time = time_diff // 60
        # 用户状态检测，是否在闭关中
        is_type, msg = check_user_type(user_id, 5)
        if is_type:
            # 虚神界闭关时长计算
            impart_data_draw = await impart_pk_check(user_id)
            impart_exp_time = int(impart_data_draw['exp_day'])
            # 余剩时间
            last_time = max(impart_exp_time - exp_time, 0)
            xiuxian_impart.use_impart_exp_day(last_time, user_id)
            is_xu_world = '虚神界'
            # 余剩时间检测
            if last_time:
                exp_time = exp_time * 6
                time_tipe = ''
            else:
                exp_time = exp_time + impart_exp_time * 5
                time_tipe = '耗尽'
            time_msg = f"{time_tipe}余剩虚神界内闭关时间：{last_time}分钟，"
        else:
            is_xu_world = ''
            time_msg = ''

        # 退出状态
        sql_message.in_closing(user_id, user_type)
        # 根据时间发送修为
        is_full, exp, result_msg = exp_up_by_time(user_info, exp_time)
        # 拼接提示
        msg = (f"{is_xu_world}闭关修炼结束，{is_full}共闭关{exp_time}分钟，{time_msg}"
               f"本次闭关共增加修为：{number_to(exp)}|{exp}{result_msg[0]}{result_msg[1]}")
    await bot.send(event=event, message=msg)
    await out_closing.finish()


@mind_state.handle(parameterless=[Cooldown(at_sender=False)])
async def mind_state_(bot: Bot, event: GroupMessageEvent):
    """我的状态信息"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    main_hp_rank = jsondata.level_data()[user_info['level']]["HP"]  # 添加血量补偿测试
    # 意义不明的回满血机制
    if user_info['hp'] is None or user_info['hp'] == 0:
        sql_message.update_user_hp(user_id)

    user_info = sql_message.get_user_real_info(user_id)
    level_rate = sql_message.get_root_rate(user_info['root_type'])  # 灵根倍率
    realm_rate = jsondata.level_data()[user_info['level']]["spend"]  # 境界倍率
    user_buff_data = UserBuffDate(user_id)
    main_buff_data = user_buff_data.get_user_main_buff_data()
    user_armor_crit_data = user_buff_data.get_user_armor_buff_data()  # 我的状态防具会心
    user_weapon_data = UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器减伤
    user_main_crit_data = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法会心
    user_main_data = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法减伤

    if user_main_data is not None:
        main_def = user_main_data['def_buff'] * 100  # 我的状态功法减伤
    else:
        main_def = 0

    if user_armor_crit_data is not None:  # 我的状态防具会心
        armor_crit_buff = ((user_armor_crit_data['crit_buff']) * 100)
    else:
        armor_crit_buff = 0

    if user_weapon_data is not None:
        crit_buff = ((user_weapon_data['crit_buff']) * 100)
    else:
        crit_buff = 0

    user_armor_data = user_buff_data.get_user_armor_buff_data()
    if user_armor_data is not None:
        def_buff = int(user_armor_data['def_buff'] * 100)  # 我的状态防具减伤
    else:
        def_buff = 0

    user_armor_data = user_buff_data.get_user_armor_buff_data()

    if user_weapon_data is not None:
        weapon_def = user_weapon_data['def_buff'] * 100  # 我的状态武器减伤
    else:
        weapon_def = 0

    if user_main_crit_data is not None:  # 我的状态功法会心
        main_crit_buff = ((user_main_crit_data['crit_buff']) * 100)
    else:
        main_crit_buff = 0

    list_all = len(OtherSet().level) - 1
    now_index = OtherSet().level.index(user_info['level'])
    if list_all == now_index:
        exp_meg = f"位面至高"
    else:
        is_updata_level = OtherSet().level[now_index + 1]
        need_exp = sql_message.get_level_power(is_updata_level)
        get_exp = need_exp - user_info['exp']
        if get_exp > 0:
            exp_meg = f"还需{number_to(get_exp)}修为可突破！"
        else:
            exp_meg = f"可突破！"

    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data is not None else 0
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    impart_data = xiuxian_impart.get_user_info_with_id(user_id)
    impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
    impart_mp_per = impart_data['impart_mp_per'] if impart_data is not None else 0
    impart_know_per = impart_data['impart_know_per'] if impart_data is not None else 0
    impart_burst_per = impart_data['impart_burst_per'] if impart_data is not None else 0
    boss_atk = impart_data['boss_atk'] if impart_data is not None else 0
    weapon_critatk_data = UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器会心伤害
    weapon_critatk = weapon_critatk_data['critatk'] if weapon_critatk_data is not None else 0  # 我的状态武器会心伤害
    user_main_critatk = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法会心伤害
    main_critatk = user_main_critatk['critatk'] if user_main_critatk is not None else 0  # 我的状态功法会心伤害
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    number = user_main_critatk["number"] if user_main_critatk is not None else 0
    now_place = place.get_place_name(place.get_now_place_id(user_id))

    msg = f"""
道号：{user_info['user_name']}
气血:{number_to(user_info['hp'])}/{number_to(int((user_info['exp'] / 2) * (1 + main_hp_buff + impart_hp_per) * main_hp_rank))}({((user_info['hp'] / ((user_info['exp'] / 2) * (1 + main_hp_buff + impart_hp_per) * (main_hp_rank)))) * 100:.2f}%)
真元:{number_to(user_info['mp'])}/{number_to(user_info['exp'])}({((user_info['mp'] / user_info['exp']) * 100):.2f}%)
攻击:{number_to(user_info['atk'])}
突破状态: {exp_meg}
(概率：{jsondata.level_rate_data()[user_info['level']] + leveluprate + number}%)
攻击修炼:{user_info['atkpractice']}级
(提升攻击力{user_info['atkpractice'] * 4}%)
修炼效率:{int(((level_rate * realm_rate) * (1 + main_buff_rate_buff)) * 100)}%
会心:{crit_buff + int(impart_know_per * 100) + armor_crit_buff + main_crit_buff}%
减伤率:{100 - (((100 - def_buff) * (100 - weapon_def) * (100 - main_def)) / 10000):.2f}%
boss战增益:{int(boss_atk * 100)}%
会心伤害增益:{int((1.5 + impart_burst_per + weapon_critatk + main_critatk) * 100)}%
当前体力：{user_info['user_stamina']}
所在位置：{now_place}
"""
    sql_message.update_last_check_info_time(user_id)
    await bot.send(event=event, message=msg)
    await mind_state.finish()


@select_state.handle(parameterless=[Cooldown(at_sender=False)])
async def select_state_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看其他角色状态信息"""

    _, user_msg, _ = check_user(event)

    user_id = user_msg['user_id']  # 需要改为获取对方id实现查看
    try:
        user_id = sql_message.get_user_id(args)  # 获取目标id
        user_msg = sql_message.get_user_info_with_id(user_id)
    except:
        await bot.send(event=event, message="修仙界中找不到此人！！")
        await select_state.finish()
    sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    try:
        main_hp_rank = jsondata.level_data()[user_msg['level']]["HP"]  # 添加血量补偿测试
    except:
        main_hp_rank = 1
        await bot.send(event=event, message="修仙界中找不到此人！！")
        await select_state.finish()
    if user_msg['hp'] is None or user_msg['hp'] == 0:
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_real_info(user_id)
    level_rate = sql_message.get_root_rate(user_msg['root_type'])  # 灵根倍率
    realm_rate = jsondata.level_data()[user_msg['level']]["spend"]  # 境界倍率
    user_buff_data = UserBuffDate(user_id)
    main_buff_data = user_buff_data.get_user_main_buff_data()
    user_armor_crit_data = user_buff_data.get_user_armor_buff_data()  # 我的状态防具会心
    user_weapon_data = UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器减伤
    user_main_crit_data = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法会心
    user_main_data = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法减伤

    if user_main_data is not None:
        main_def = user_main_data['def_buff'] * 100  # 我的状态功法减伤
    else:
        main_def = 0

    if user_armor_crit_data is not None:  # 我的状态防具会心
        armor_crit_buff = ((user_armor_crit_data['crit_buff']) * 100)
    else:
        armor_crit_buff = 0

    if user_weapon_data is not None:
        crit_buff = ((user_weapon_data['crit_buff']) * 100)
    else:
        crit_buff = 0

    user_armor_data = user_buff_data.get_user_armor_buff_data()
    if user_armor_data is not None:
        def_buff = int(user_armor_data['def_buff'] * 100)  # 我的状态防具减伤
    else:
        def_buff = 0

    user_armor_data = user_buff_data.get_user_armor_buff_data()

    if user_weapon_data is not None:
        weapon_def = user_weapon_data['def_buff'] * 100  # 我的状态武器减伤
    else:
        weapon_def = 0

    if user_main_crit_data is not None:  # 我的状态功法会心
        main_crit_buff = ((user_main_crit_data['crit_buff']) * 100)
    else:
        main_crit_buff = 0

    list_all = len(OtherSet().level) - 1
    now_index = OtherSet().level.index(user_msg['level'])
    if list_all == now_index:
        exp_meg = f"位面至高"
    else:
        is_updata_level = OtherSet().level[now_index + 1]
        need_exp = sql_message.get_level_power(is_updata_level)
        get_exp = need_exp - user_msg['exp']
        if get_exp > 0:
            exp_meg = f"还需{number_to(get_exp)}修为可突破！"
        else:
            exp_meg = f"可突破！"

    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data is not None else 0
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    impart_data = xiuxian_impart.get_user_info_with_id(user_id)
    impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
    impart_mp_per = impart_data['impart_mp_per'] if impart_data is not None else 0
    impart_know_per = impart_data['impart_know_per'] if impart_data is not None else 0
    impart_burst_per = impart_data['impart_burst_per'] if impart_data is not None else 0
    boss_atk = impart_data['boss_atk'] if impart_data is not None else 0
    weapon_critatk_data = UserBuffDate(user_id).get_user_weapon_data()  # 我的状态武器会心伤害
    weapon_critatk = weapon_critatk_data['critatk'] if weapon_critatk_data is not None else 0  # 我的状态武器会心伤害
    user_main_critatk = UserBuffDate(user_id).get_user_main_buff_data()  # 我的状态功法会心伤害
    main_critatk = user_main_critatk['critatk'] if user_main_critatk is not None else 0  # 我的状态功法会心伤害
    leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    number = user_main_critatk["number"] if user_main_critatk is not None else 0

    msg = f"""
道号：{user_msg['user_name']}
气血:{number_to(user_msg['hp'])}/{number_to(int((user_msg['exp'] / 2) * (1 + main_hp_buff + impart_hp_per) * main_hp_rank))}({((user_msg['hp'] / ((user_msg['exp'] / 2) * (1 + main_hp_buff + impart_hp_per) * (main_hp_rank)))) * 100:.2f}%)
真元:{number_to(user_msg['mp'])}/{number_to(user_msg['exp'])}({((user_msg['mp'] / user_msg['exp']) * 100):.2f}%)
攻击:{number_to(user_msg['atk'])}
攻击修炼:{user_msg['atkpractice']}级
修炼效率:{int(((level_rate * realm_rate) * (1 + main_buff_rate_buff)) * 100)}%
会心:{crit_buff + int(impart_know_per * 100) + armor_crit_buff + main_crit_buff}%
减伤率:{100 - (((100 - def_buff) * (100 - weapon_def) * (100 - main_def)) / 10000):.2f}%
boss战增益:{int(boss_atk * 100)}%
会心伤害增益:{int((1.5 + impart_burst_per + weapon_critatk + main_critatk) * 100)}%
"""
    sql_message.update_last_check_info_time(user_id)
    await bot.send(event=event, message=msg)
    await select_state.finish()


@buffinfo.handle(parameterless=[Cooldown(at_sender=False)])
async def buffinfo_(bot: Bot, event: GroupMessageEvent):
    """我的功法"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    mainbuffdata = UserBuffDate(user_id).get_user_main_buff_data()
    if mainbuffdata is not None:
        s, mainbuffmsg = get_main_info_msg(str(get_user_buff(user_id)['main_buff']))
    else:
        mainbuffmsg = ''

    subbuffdata = UserBuffDate(user_id).get_user_sub_buff_data()  # 辅修功法13
    if subbuffdata is not None:
        sub, subbuffmsg = get_sub_info_msg(str(get_user_buff(user_id)['sub_buff']))
    else:
        subbuffmsg = ''

    secbuffdata = UserBuffDate(user_id).get_user_sec_buff_data()
    secbuffmsg = get_sec_msg(secbuffdata) if get_sec_msg(secbuffdata) != '无' else ''
    msg = f"""
道友的主功法：{mainbuffdata["name"] if mainbuffdata is not None else '无'}
{mainbuffmsg}
道友的辅修功法：{subbuffdata["name"] if subbuffdata is not None else '无'}
{subbuffmsg}
道友的神通：{secbuffdata["name"] if secbuffdata is not None else '无'}
{secbuffmsg}
"""

    await bot.send(event=event, message=msg)
    await buffinfo.finish()


@del_exp_decimal.handle(parameterless=[Cooldown(at_sender=False)])
async def del_exp_decimal_(bot: Bot, event: GroupMessageEvent):
    """清除修为浮点数"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    exp = user_info['exp']
    sql_message.del_exp_decimal(user_id, exp)
    msg = f"黑暗动乱暂时抑制成功！"
    await bot.send(event=event, message=msg)
    await del_exp_decimal.finish()


@my_exp_num.handle(parameterless=[Cooldown(at_sender=False)])
async def my_exp_num_(bot: Bot, event: GroupMessageEvent):
    """我的双修次数"""
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    two_exp_num = two_exp_cd.find_user(user_id)
    impart_data = xiuxian_impart.get_user_info_with_id(user_id)
    impart_two_exp = impart_data['impart_two_exp'] if impart_data is not None else 0

    main_two_data = UserBuffDate(user_id).get_user_main_buff_data()
    main_two = main_two_data['two_buff'] if main_two_data is not None else 0

    num = (two_exp_limit + impart_two_exp + main_two) - two_exp_num
    if num <= 0:
        num = 0
    msg = f"道友剩余双修次数{num}次！"
    await bot.send(event=event, message=msg)
    await my_exp_num.finish()
