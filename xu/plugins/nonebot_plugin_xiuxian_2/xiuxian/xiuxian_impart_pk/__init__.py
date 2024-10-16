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
impart_pk_now = on_command("虚神界对决", priority=15, permission=GROUP, block=True)
impart_pk_exp = on_command("虚神界闭关", aliases={"进入虚神界修炼", "闭关虚神界"},priority=8, permission=GROUP, block=True)


# 每日0点重置用虚神界次数
@impart_re.scheduled_job("cron", hour=0, minute=0)
async def impart_re_():
    impart_pk.re_data()
    xu_world.re_data()
    logger.opt(colors=True).info(f"<green>已重置虚神界次数</green>")


@impart_pk_now.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def impart_pk_now_(bot: Bot, event: GroupMessageEvent):
    """虚神界对决"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()
    user_id = user_info['user_id']
    sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    impart_data_draw = await impart_pk_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()
    user_data = impart_pk.find_user_data(user_info['user_id'])

    if user_data["pk_num"] <= 0:
        msg = f"道友今日次数耗尽，明天再来吧！"
        await bot.send(event=event, message=msg)
        await impart_pk_now.finish()

    player_1_stones = 0
    player_2_stones = 0
    combined_msg = ""
    duel_count = 0
    while user_data["pk_num"] > 0:
        duel_count += 1
        msg, win = await impart_pk_uitls.impart_pk_now_msg_to_bot(user_info['user_name'], NICKNAME)
        if win == 1:
            msg += f"战报：道友{user_info['user_name']}获胜,获得思恋结晶3颗\n"
            impart_pk.update_user_data(user_info['user_id'], False)
            xiuxian_impart.update_stone_num(3, user_id, 1)
            player_1_stones += 3
        elif win == 2:
            msg += f"战报：道友{user_info['user_name']}败了,获得思恋结晶2颗\n"
            impart_pk.update_user_data(user_info['user_id'], False)
            xiuxian_impart.update_stone_num(2, user_id, 1)
            player_1_stones += 2
            if impart_pk.find_user_data(user_id)["pk_num"] <= 0 and xu_world.check_xu_world_user_id(user_id) is True:
                msg += "检测到道友次数已用尽，已帮助道友退出虚神界！"
                xu_world.del_xu_world(user_id)
        else:
            msg = f"挑战失败"
            combined_msg += f"{msg}\n"
            break

        combined_msg += f"☆------------第{duel_count}次------------☆\n{msg}\n"
        user_data = impart_pk.find_user_data(user_info['user_id'])

    combined_msg += f"总计：道友{user_info['user_name']}获得思恋结晶{player_1_stones}颗\n"

    await bot.send(event=event, message=combined_msg)
    await impart_pk_now.finish()


@impart_pk_exp.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_pk_exp_(bot: Bot, event: GroupMessageEvent):
    """虚神界闭关"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
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




        
