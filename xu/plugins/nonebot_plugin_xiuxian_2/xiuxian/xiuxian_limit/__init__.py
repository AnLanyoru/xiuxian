import pickle

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
offset = on_command('补偿', priority=1, permission=GROUP, block=True)
offset_get = on_command('领取补偿', priority=1, permission=GROUP, block=True)
get_log = on_command('查日志', aliases={"日志查询", "查询日志", "查看日志", "日志记录"}, priority=1, permission=GROUP, block=True)
get_shop_log = on_command('坊市日志', aliases={"查询坊市日志", "查看坊市日志"}, priority=1, permission=GROUP, block=True)


@offset.handle(parameterless=[Cooldown(cd_time=30, at_sender=False)])
async def offset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
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


@offset_get.handle(parameterless=[Cooldown(cd_time=3, at_sender=False)])
async def offset_get_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await offset.finish()
    user_id = user_info['user_id']
    num_msg = get_num_from_str(args.extract_plain_text())
    num = int(num_msg[0]) if num_msg else 1
    offset_info = LimitData().get_offset_by_id(num)
    if not offset_info:  # 补偿合理性检测
        msg = f"不存在ID为 {num}，的补偿，请检查！！"
        await bot.send(event=event, message=msg)
        await offset.finish()
    is_pass = LimitHandle().update_user_offset(user_id, num)  # 申领检查
    if not is_pass:
        msg = f"你已领取补偿【{offset_info['offset_name']}】，请不要重复申领！！"
        await bot.send(event=event, message=msg)
        await offset.finish()
    # 检查通过，发放奖励
    items_info = offset_info.get("offset_items")
    msg = "领取补偿成功：\n获取了：\n"
    for item_id in items_info:
        item_id = str(item_id)
        item_info = items.items.get(item_id)
        if item_info:
            item_name = item_info['name']
            item_type = item_info['type']
            item_num = items_info[int(item_id)]
            sql_message.send_back(user_id, item_id, item_name, item_type, item_num, 1)
            msg += f"\n{item_name} {item_num}个！"
        else:
            msg += f"\n不存在的物品 0个"
    if offset_info['daily_update']:
        msg += "\n明天还可继续领取哦！！"
    await bot.send(event=event, message=msg)
    await offset.finish()


@get_log.handle(parameterless=[Cooldown(cd_time=30, at_sender=False)])
async def offset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await get_log.finish()
    user_id = user_info['user_id']
    logs = LimitHandle().get_user_log_data(user_id)
    if logs:
        await send_msg_handler(bot, event, '日志', bot.self_id, logs)
        await get_log.finish()
    else:
        msg = "未查询到道友的日志信息！"
        await bot.send(event=event, message=msg)
        await get_log.finish()


@get_shop_log.handle(parameterless=[Cooldown(cd_time=30, at_sender=False)])
async def offset_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 这里曾经是风控模块，但是已经不再需要了
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await get_shop_log.finish()
    user_id = user_info['user_id']
    logs = LimitHandle().get_user_shop_log_data(user_id)
    if logs:
        await send_msg_handler(bot, event, '坊市日志', bot.self_id, logs)
        await get_shop_log.finish()
    else:
        msg = "未查询到道友的坊市日志信息！"
        await bot.send(event=event, message=msg)
        await get_shop_log.finish()

