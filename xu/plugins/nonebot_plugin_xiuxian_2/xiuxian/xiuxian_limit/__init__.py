from .limit_database import LimitData, LimitHandle
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
    check_user, get_msg_pic, get_num_from_str, send_msg_handler
)
from ..xiuxian_utils.item_json import Items

items = Items()
sql_message = XiuxianDateManage()  # sql类
limit = LimitData()
offset = on_command('补偿', priority=15, permission=GROUP, block=True)
offset_get = on_command('领取补偿', priority=15, permission=GROUP, block=True)


@offset.handle(parameterless=[Cooldown(at_sender=False)])
async def offset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await offset.finish()
    user_id = user_info['user_id']
    msg_list = LimitHandle().get_all_user_offset_msg(user_id)  # 存入需要被翻页的数据
    if msg_list:
        page_msg = get_num_from_str(args.extract_plain_text())
        items_all = len(msg_list)
        per_item = 3  # 每页物品数量
        page_all = ((items_all // per_item) + 1) if (items_all % per_item != 0) else (items_all // per_item)  # 总页数
        page = int(page_msg[0]) if page_msg else 1
        if page_all < page:
            msg = "\n补偿没有那么多页！！！"
            await bot.send(event=event, message=msg)
            await offset.finish()
        item_num = page * per_item - per_item
        item_num_end = item_num + per_item
        msg_hand = ["当前可领补偿如下："]  # 页面头
        page_info = [f"第{page}/{page_all}页\n——tips——\n可以发送 补偿 页数 来查看更多页\n领取补偿 补偿id 来领取补偿哦"]  # 页面尾
        msg_list = msg_hand + msg_list[item_num:item_num_end] + page_info
        pass
    else:
        msg = "\n补偿列表当前空空如也！！！"
        await bot.send(event=event, message=msg)
        await offset.finish()
    await send_msg_handler(bot, event, '补偿列表', bot.self_id, msg_list)
    await offset.finish()
