import random
from datetime import datetime
from nonebot import get_bots, on_command, require, on_fullmatch
from nonebot.params import CommandArg

from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER,
    MessageSegment
)
from .old_rift_info import old_rift_info
from .. import DRIVER
from ..xiuxian_place import Place
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.utils import (
    check_user, check_user_type,
    send_msg_handler, get_msg_pic, CommandObjectID
)
from .riftconfig import get_rift_config, savef_rift
from .jsondata import save_rift_data, read_rift_data
from ..xiuxian_config import XiuConfig
from .riftmake import (
    Rift, get_rift_type, get_story_type, NONEMSG, get_battle_type,
    get_dxsj_info, get_boss_battle_info, get_treasure_info
)


config = get_rift_config()
groups = config['open']  # list，群发秘境开启信息
sql_message = XiuxianDateManage()  # sql类
cache_help = {}
world_rift = {}  # dict
# 定时任务
set_rift = require("nonebot_plugin_apscheduler").scheduler

explore_rift = on_fullmatch("探索秘境", priority=5, permission=GROUP, block=True)
rift_help = on_fullmatch("秘境帮助", priority=6, permission=GROUP, block=True)
create_rift = on_fullmatch("生成秘境", priority=5, permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER), block=True)
complete_rift = on_command("秘境结算", aliases={"结算秘境"}, priority=7, permission=GROUP, block=True)

# 秘境类改动，将原group分隔的群秘境形式更改为位置（依旧套用group），位置实现方式为位置与状态压成元组，原状态访问[0]数据，位置访问[1]数据
__rift_help__ = f"""
\n———秘境帮助———
1、探索秘境:
>消耗240点体力探索秘境获取随机奖励
2、秘境结算:
>结算秘境奖励
>获取秘境帮助信息
——————————————
tips：每天早八各位面将会生成一个随机等级的秘境供各位道友探索
""".strip()


@DRIVER.on_startup
async def read_rift_():
    global world_rift
    world_rift.update(old_rift_info.read_rift_info())
    logger.opt(colors=True).info(f"<green>历史rift数据读取成功</green>")


@DRIVER.on_shutdown
async def save_rift_():
    global world_rift
    old_rift_info.save_rift(world_rift)
    logger.opt(colors=True).info(f"<green>rift数据已保存</green>")


# 定时任务生成秘境，原群私有，改公有
@set_rift.scheduled_job("cron", hour=8, minute=0)
async def set_rift_():
    global world_rift  # 挖坑，不同位置的秘境
    if Place().get_worlds():
        world_rift = {}
        for world_id in Place().get_worlds():
            if world_id == len(Place().get_worlds())-1:
                continue
            rift = Rift()
            rift.name = get_rift_type()
            place_all_id = [place for place in Place().get_world_place_list(world_id)]
            place_id = random.choice(place_all_id)
            rift.place = place_id
            rift.rank = config['rift'][rift.name]['rank']
            rift.count = config['rift'][rift.name]['count']
            rift.time = config['rift'][rift.name]['time']
            world_rift[world_id] = rift
            world_name = Place().get_world_name(place_id)
            place_name = Place().get_place_name(place_id)
            msg = (f"秘境：【{rift.name}】已在【{world_name}】的【{place_name}】开启！\n"
                   f"请诸位身在{world_name}的道友前往{place_name}(ID:{place_id})发送 探索秘境 来加入吧！")


@rift_help.handle(parameterless=[Cooldown(at_sender=False)])
async def rift_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """秘境帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help[session_id]))
        await rift_help.finish()
    else:
        msg = __rift_help__
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await rift_help.finish()


@create_rift.handle(parameterless=[Cooldown(at_sender=False)])
async def create_rift_(bot: Bot, event: GroupMessageEvent):
    """
    生成秘境，格式为 生成秘境 位置 秘境名称（可不填）//未完成
    :param bot:
    :param event:
    :return:
    """
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    global world_rift  # 挖坑，不同位置的秘境
    if Place().get_worlds():
        world_rift = {}
        for world_id in Place().get_worlds():
            if world_id == len(Place().get_worlds())-1:
                continue
            rift = Rift()
            rift.name = get_rift_type()
            place_all_id = [place for place in Place().get_world_place_list(world_id)]
            place_id = random.choice(place_all_id)
            rift.place = place_id
            rift.rank = config['rift'][rift.name]['rank']
            rift.count = config['rift'][rift.name]['count']
            rift.time = config['rift'][rift.name]['time']
            world_rift[world_id] = rift
            world_name = Place().get_world_name(place_id)
            place_name = Place().get_place_name(place_id)
            msg = (f"秘境：【{rift.name}】已在【{world_name}】的【{place_name}】开启！\n"
                   f"请诸位身在{world_name}的道友前往{place_name}(ID:{place_id})发送 探索秘境 来加入吧！")
            await bot.send_group_msg(group_id=send_group_id, message=msg)
    await create_rift.finish()


@explore_rift.handle(parameterless=[Cooldown(stamina_cost=240, at_sender=False)])
async def _(bot: Bot, event: GroupMessageEvent):
    """探索秘境"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await explore_rift.finish()

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)  # 需要无状态的用户
    if not is_type:
        sql_message.update_user_stamina(user_id, 240, 1)
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await explore_rift.finish()
    else:
        place_id = Place().get_now_place_id(user_id)
        world_id = Place().get_world_id(place_id)
        world_name = Place().get_world_name(place_id)
        place_name = Place().get_place_name(place_id)
        try:
            world_rift[world_id]
        except KeyError:
            msg = f'道友所在位面【{world_name}】尚未有秘境出世，请道友耐心等待!'
            sql_message.update_user_stamina(user_id, 240, 1)
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await explore_rift.finish()
        if place_id == world_rift[world_id].place:
            msg = f"道友进入秘境：{world_rift[world_id].name}，探索需要花费体力240点！！，余剩体力{user_info['user_stamina']}/2400！"
            rift_data = {
                "name": world_rift[world_id].name,
                "time": world_rift[world_id].time,
                "rank": world_rift[world_id].rank
            }

            save_rift_data(user_id, rift_data)
            sql_message.do_work(user_id, 3, rift_data["time"])
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await explore_rift.finish()
        else:
            far, start_place, to_place = Place().get_distance(place_id, world_rift[world_id].place)
            sql_message.update_user_stamina(user_id, 240, 1)
            msg = f"道友所在位置没有秘境出世，当前位面【{world_name}】的秘境【{world_rift[world_id].name}】在距你{far:.1f}万里的：【{to_place}】，"
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await explore_rift.finish()


@complete_rift.handle(parameterless=[Cooldown(at_sender=False)])
async def complete_rift_(bot: Bot, event: GroupMessageEvent):
    """秘境结算"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await complete_rift.finish()

    user_id = user_info['user_id']

    is_type, msg = check_user_type(user_id, 3)  # 需要在秘境的用户
    if not is_type:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await complete_rift.finish()
    else:
        rift_info = None
        try:
            rift_info = read_rift_data(user_id)
        except:
            msg = '发生未知错误！'
            sql_message.do_work(user_id, 0)
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await complete_rift.finish()
        sql_message.do_work(user_id, 0)
        rift_rank = rift_info["rank"]  # 秘境等级
        rift_type = get_story_type()  # 无事、宝物、战斗
        if rift_type == "无事":
            msg = random.choice(NONEMSG)
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await complete_rift.finish()
        elif rift_type == "战斗":
            rift_type = get_battle_type()
            if rift_type == "掉血事件":
                msg = get_dxsj_info("掉血事件", user_info)
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await complete_rift.finish()
            elif rift_type == "Boss战斗":
                result, msg = await get_boss_battle_info(user_info, rift_rank, bot.self_id)
                await send_msg_handler(bot, event, result)
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await complete_rift.finish()
        elif rift_type == "宝物":
            msg = get_treasure_info(user_info, rift_rank)
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await complete_rift.finish()


def is_in_groups(event: GroupMessageEvent):
    return str(event.group_id) in groups
