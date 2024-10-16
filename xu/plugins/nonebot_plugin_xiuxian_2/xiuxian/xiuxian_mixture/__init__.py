from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot.params import CommandArg
from nonebot import on_command
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment
)
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic
)
from ..xiuxian_utils.item_json import Items

items = Items()
sql_message = XiuxianDateManage()  # sql类
mixture = on_command('合成', priority=15, permission=GROUP,block=True)


@mixture.handle(parameterless=[Cooldown(at_sender=False)])
async def use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await mixture.finish()
    user_id = user_info['user_id']
    back_msg = sql_message.get_back_msg(user_id)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        await bot.send(event=event, message=msg)
        await mixture.finish()



