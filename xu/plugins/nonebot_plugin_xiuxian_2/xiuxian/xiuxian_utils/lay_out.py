import random
from nonebot.log import logger
from nonebot import get_bots, get_bot, require
from enum import IntEnum, auto
from collections import defaultdict
from asyncio import get_running_loop
from typing import DefaultDict, Dict, Any
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from ..xiuxian_config import XiuConfig, JsonConfig
from .xiuxian2_handle import XiuxianDateManage

sql_message = XiuxianDateManage()

limit_all_message = require("nonebot_plugin_apscheduler").scheduler
limit_all_stamina = require("nonebot_plugin_apscheduler").scheduler
auto_recover_hp = require("nonebot_plugin_apscheduler").scheduler

limit_all_data: Dict[str, Any] = {}
limit_message_num = XiuConfig().message_limit
limit_message_time = XiuConfig().message_limit_time

#
# @auto_recover_hp.scheduled_job('interval', minutes=1)
# def auto_recover_hp_():
#     """
#     不要使用会变得不幸
#     :return:
#     """
#     # sql_message.auto_recover_hp()
#     pass
#


@limit_all_message.scheduled_job('interval', seconds=limit_message_time)
def limit_all_message_():
    # 重置消息字典
    global limit_all_data
    limit_all_data = {}
    logger.opt(colors=True).success(f"<green>已重置消息每{format_time(limit_message_time)}限制！</green>")


@limit_all_stamina.scheduled_job('interval', minutes=1)
def limit_all_stamina_():
    # 恢复体力
    sql_message.update_all_users_stamina(XiuConfig().max_stamina, XiuConfig().stamina_recovery_points)


def limit_all_run(user_id: str):
    user_id = str(user_id)
    user_limit_data = limit_all_data.get(user_id)
    if user_limit_data:
        pass
    else:
        limit_all_data[user_id] = {"num": 0,
                                   "tip": False}
    num = limit_all_data[user_id]["num"]
    tip = limit_all_data[user_id]["tip"]
    num += 1
    if num > limit_message_num and tip is False:
        tip = True
        limit_all_data[user_id]["num"] = num
        limit_all_data[user_id]["tip"] = tip
        return True
    if num > limit_message_num and tip is True:
        limit_all_data[user_id]["num"] = num
        return False
    else:
        limit_all_data[user_id]["num"] = num
        return None


def format_time(seconds: int) -> str:
    """将秒数转换为更大的时间单位"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{days}天{hours}小时{minutes}分钟{seconds}秒"
    elif hours > 0:
        return f"{hours}小时{minutes}分钟{seconds}秒"
    elif minutes > 0:
        return f"{minutes}分钟{seconds}秒"
    else:
        return f"{seconds}秒"


def get_random_chat_notice():
    return random.choice([
        "等待{}，让我再歇会！",
        "冷静一下，还有{}，让我再歇会！",
        "时间还没到，还有{}，歇会歇会~~"
    ])


class CooldownIsolateLevel(IntEnum):
    """命令冷却的隔离级别"""

    GLOBAL = auto()
    GROUP = auto()
    USER = auto()
    GROUP_USER = auto()


def Cooldown(
        cd_time: float = 2,
        at_sender: bool = True,
        isolate_level: CooldownIsolateLevel = CooldownIsolateLevel.USER,
        parallel: int = 1,
        stamina_cost: int = 0,
        check_user: bool = True
) -> None:
    """依赖注入形式的命令冷却

    用法:
        ```python
        @matcher.handle(parameterless=[Cooldown(cooldown=11.4514, ...)])
        async def handle_command(matcher: Matcher, message: Message):
            ...
        ```

    参数:
        cd_time: 命令冷却间隔
        at_sender: 是否at
        isolate_level: 命令冷却的隔离级别, 参考 `CooldownIsolateLevel`
        parallel: 并行执行的命令数量
        stamina_cost: 每次执行命令消耗的体力值
    """
    if not isinstance(isolate_level, CooldownIsolateLevel):
        raise ValueError(
            f"invalid isolate level: {isolate_level!r}, "
            "isolate level must use provided enumerate value."
        )
    running: DefaultDict[str, int] = defaultdict(lambda: parallel)
    time_sy: Dict[str, int] = {}

    def increase(key: str, value: int = 1):
        running[key] += value
        if running[key] >= parallel:
            del running[key]
            del time_sy[key]
        return

    async def dependency(bot: Bot, matcher: Matcher, event: MessageEvent):
        user_id = str(event.get_user_id())
        limit_type = limit_all_run(user_id)
        # 发言限制，请前往xiuxian_config设置
        if limit_type is True:
            too_fast_notice = f"道友的发言频率超过了每{format_time(limit_message_time)}{limit_message_num}条限制，缓会儿！！"
            await bot.send(event=event, message=too_fast_notice)
            await matcher.finish()
        elif limit_type is False:
            await matcher.finish()
        else:
            pass

        # 消息长度限制
        message = event.raw_message
        message_len = len(message)
        if message_len > 70:
            too_long_message_notice = f"道友的话也太复杂了，我头好晕！！！"
            await bot.send(event=event, message=too_long_message_notice)
            await matcher.finish()

        loop = get_running_loop()

        if isolate_level is CooldownIsolateLevel.GROUP:
            key = str(
                event.group_id
                if isinstance(event, GroupMessageEvent)
                else event.user_id,
            )
        elif isolate_level is CooldownIsolateLevel.USER:
            key = str(event.user_id)
        elif isolate_level is CooldownIsolateLevel.GROUP_USER:
            key = (
                f"{event.group_id}_{event.user_id}"
                if isinstance(event, GroupMessageEvent)
                else str(event.user_id)
            )
        else:
            key = CooldownIsolateLevel.GLOBAL.name
        if running[key] <= 0:
            if cd_time >= 1.5:
                time = int(cd_time - (loop.time() - time_sy[key]))
                if time <= 1:
                    time = 1
                formatted_time = format_time(time)
                await bot.send(event=event,
                               message=get_random_chat_notice().format(formatted_time))
                await matcher.finish()
            else:
                await matcher.finish()
        else:
            time_sy[key] = int(loop.time())
            running[key] -= 1
            loop.call_later(cd_time, lambda: increase(key))

        # 用户检查

        user_id = int(user_id)
        user_info = sql_message.get_user_info_with_id(user_id)
        if user_info is None and check_user is True:
            msg = "修仙界没有道友的信息，请输入【踏入仙途】加入！"
            await bot.send(event=event, message=msg)
            await matcher.finish()

        if stamina_cost:
            if user_info['user_stamina'] < stamina_cost and XiuConfig().stamina_open is True:
                msg = f"你没有足够的体力，请等待体力恢复后再试！\r本次行动需要消耗：{stamina_cost}体力值\r当前体力值：{user_info['user_stamina']}/2400"
                await bot.send(event=event, message=msg)
                await matcher.finish()
            sql_message.update_user_stamina(user_id, stamina_cost, 2)  # 减少体力
        return

    return Depends(dependency)


put_bot = XiuConfig().put_bot
main_bot = XiuConfig().main_bo
layout_bot_dict = XiuConfig().layout_bot_dict



