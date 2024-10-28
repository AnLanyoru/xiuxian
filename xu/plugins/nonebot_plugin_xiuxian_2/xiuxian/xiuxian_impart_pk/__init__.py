import random

from nonebot import on_command, require, on_fullmatch
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)

from ..xiuxian_impart import impart_check
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from ..xiuxian_utils.data_source import jsondata
from nonebot.log import logger
from ..xiuxian_utils.utils import check_user, get_msg_pic, send_msg_handler, check_user_type, get_num_from_str
from .impart_pk_uitls import impart_pk_check
from .xu_world import xu_world
from .impart_pk import impart_pk
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage, OtherSet, UserBuffDate, XIUXIAN_IMPART_BUFF
from .. import NICKNAME

xiuxian_impart = XIUXIAN_IMPART_BUFF()
sql_message = XiuxianDateManage()  # sql类

impart_re = require("nonebot_plugin_apscheduler").scheduler
impart_pk_now = on_command("虚神界对决", priority=3, permission=GROUP, block=True)
impart_pk_exp = on_command("虚神界闭关", aliases={"进入虚神界修炼"}, priority=3, permission=GROUP, block=True)


# 每日0点重置用虚神界次数
@impart_re.scheduled_job("cron", hour=0, minute=0)
async def impart_re_():
    impart_pk.re_data()
    logger.opt(colors=True).info(f"<green>已重置虚神界次数</green>")


@impart_pk_now.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def impart_pk_now_(bot: Bot, event: GroupMessageEvent):
    """虚神界对决"""
    # 这里曾经是风控模块，但是已经不再需要了
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()
    user_id = user_info['user_id']
    pk_num = impart_pk.get_impart_pk_num(user_id)
    if pk_num:
        msg = f"道友今日已经对决过了，明天再来吧！"
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()
    await impart_check(user_id)
    impart_pk.update_impart_pk_num(user_id)
    stones = random.randint(6, 9)
    await xiuxian_impart.update_stone_num(stones, user_id, 1)
    combined_msg = f"\n进入虚神界与{NICKNAME}对决，将{NICKNAME}击败{stones}次，获得思恋结晶{stones}颗"
    await bot.send(event=event, message=combined_msg)
    await impart_pk_now.finish()


@impart_pk_exp.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_pk_exp_(bot: Bot, event: GroupMessageEvent):
    """虚神界闭关"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_type = 5  # 状态0为无事件
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await impart_pk_exp.finish()
    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)
    if is_type:  # 符合
        impart_data_draw = await impart_pk_check(user_id)  # 虚神界余剩闭关时间
        if int(impart_data_draw['exp_day']) > 0:
            sql_message.in_closing(user_id, user_type)
            msg = f"进入虚神界，开始闭关，余剩虚神界内加速修炼时间：{int(impart_data_draw['exp_day'])}分钟，如需出关，发送【出关】！"
            await bot.send(event=event, message=msg)
            await impart_pk_exp.finish()
        else:
            msg = "道友虚神界内修炼余剩时长不足"
            await bot.send(event=event, message=msg)
            await impart_pk_exp.finish()
    else:
        await bot.send(event=event, message=msg)
        await impart_pk_exp.finish()




        
