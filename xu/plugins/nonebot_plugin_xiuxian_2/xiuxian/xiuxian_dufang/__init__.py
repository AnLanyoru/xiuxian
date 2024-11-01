import random
from re import I
from typing import Any, Tuple
from ..xiuxian_utils.lay_out import Cooldown
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.params import RegexGroup
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic,
    CommandObjectID
)
cache_help = {}
sql_message = XiuxianDateManage()  # sql类

__dufang_help__ = f"""
虽然不知道你怎么找到这来的
但是，还请你回去，这个功能已经被我完全拆了
""".strip()
dufang_help = on_command("金银阁帮助", permission=GROUP, priority=7, block=True)


@dufang_help.handle(parameterless=[Cooldown(at_sender=False)])
async def dufang_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):

    msg = __dufang_help__
    await bot.send(event=event, message=msg)
    await dufang_help.finish()
