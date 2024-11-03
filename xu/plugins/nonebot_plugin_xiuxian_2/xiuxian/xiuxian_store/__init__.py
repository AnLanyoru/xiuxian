import asyncio
import random
from datetime import datetime
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)

from .store_database import user_store
from ..xiuxian_utils.clean_utils import get_args_num, get_paged_msg
from ..xiuxian_utils.lay_out import Cooldown
from nonebot.params import CommandArg, RawCommand
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.utils import (
    check_user,
    send_msg_handler, get_id_from_str
)


check_user_want_item = on_command("个人摊位查看", aliases={"查看个人摊位"}, priority=8, permission=GROUP, block=True)
user_sell_to = on_command("个人摊位出售", priority=8, permission=GROUP, block=True)
user_want_item = on_command("个人摊位求购", priority=8, permission=GROUP, block=True)


@check_user_want_item.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def check_user_want_item_(bot: Bot,                      # 机器人实例
                                event: GroupMessageEvent,      # 消息主体
                                cmd: str = RawCommand(),       # 获取命令名称，用于标识翻页
                                args: Message = CommandArg()   # 获取命令参数
                                ):
    """
    查看目标用户求购物品
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    args_str = args.extract_plain_text()
    # 获取查看用户id
    look_user_id = get_id_from_str(args_str)
    # 获取查看页数
    page = get_args_num(args_str, 2)
    page = page if page else 1
    # 获取总数据
    msg_list = user_store.check_user_want_all(look_user_id)
    # 翻页化数据
    msg_list = get_paged_msg(msg_list, page, cmd)
    await send_msg_handler(bot, event, msg_list)
    await check_user_want_item.finish()


@user_want_item.handle(parameterless=[Cooldown(at_sender=False)])
async def user_want_item_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """购物"""
    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']

    await bot.send(event=event, message=msg)
    await user_want_item.finish()

