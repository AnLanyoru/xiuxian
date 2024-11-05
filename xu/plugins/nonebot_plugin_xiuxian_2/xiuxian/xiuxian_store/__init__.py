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
    send_msg_handler, get_id_from_str, get_strs_from_str, number_to
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

check_user_want_item = on_command("灵宝楼求购查看", aliases={"查看灵宝楼求购", "个人摊位查看"}, priority=8, permission=GROUP, block=True)
user_sell_to = on_command("灵宝楼出售", aliases={"个人摊位出售"}, priority=8, permission=GROUP, block=True)
user_want_item = on_command("灵宝楼求购", aliases={"个人摊位求购"}, priority=8, permission=GROUP, block=True)
check_my_want_item = on_command("我的灵宝楼求购", aliases={"我的摊位"}, priority=8, permission=GROUP, block=True)


@user_sell_to.handle(
    parameterless=[
        Cooldown(
            cd_time=2,
            at_sender=False)])
async def user_sell_to_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
        args: Message = CommandArg()  # 获取命令参数
):
    """
    个人摊位出售
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    args_str = args.extract_plain_text()
    # 获取查看页数
    sell_item_num = get_args_num(args_str, 1)
    sell_item_num = sell_item_num if sell_item_num else 1
    arg_strs = get_strs_from_str(args_str)
    item_name = arg_strs[0] if arg_strs else None
    item_id = items.items_map.get(item_name)
    if not item_id:
        msg = "物品不存在！！！"
        await bot.send(event, msg)
        await user_sell_to.finish()
    # 使用定向查找，检查物品（可选下策，遍历背包）
    item_in_back = sql_message.get_item_by_good_id_and_user_id(user_id, item_id)
    if not item_in_back:
        msg = f"道友的包内没有{item_name}！！！"
        await bot.send(event, msg)
        await user_sell_to.finish()
    # 物品数量检查
    item_num = item_in_back['goods_num'] - item_in_back['bind_num']
    if item_num < sell_item_num:
        msg = (f"道友的包内没有那么多可交易{item_name}！！！\n"
               f"当前拥有：{item_in_back['goods_num']}个\n"
               f"绑定数量：{item_in_back['bind_num']}个")
        await bot.send(event, msg)
        await user_sell_to.finish()
    # 指定用户出售判定（如果有）
    want_user_name = arg_strs[2] if arg_strs else None
    if want_user_name:
        want_user_id = sql_message.get_user_id(want_user_name)
        if not want_user_id:
            msg = f"修仙界中没有此人的踪迹！！！"
            await bot.send(event, msg)
            await user_sell_to.finish()
        want_item = user_store.check_user_want_item(want_user_id, item_id, 1)
        if not want_item:
            msg = f"{want_user_name}道友现在似乎对{item_name}不感兴趣！！！！"
            await bot.send(event, msg)
            await user_sell_to.finish()
        want_item_num = want_item['need_items_num']
        want_item_price = want_item['need_items_price']
        get_stone = want_item_price * sell_item_num
        if want_item_num:  # 有数量限制
            # 卖的太多啦！！！！人家收不下！
            if not want_item_num > sell_item_num:
                msg = f"{want_user_name}道友仅需要{want_item_num}个{item_name}！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
            want_item['need_items_num'] -= sell_item_num
        else:  # 无数量限制，检查资金是否充足
            want_item_funds = user_store.get_user_funds()  # todo
            if not get_stone > want_item_funds:  # 资金不足
                msg = f"{want_user_name}道友的资金储备不足，无法收购如此多的{item_name}！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
                user_store.update_user_funds(want_user_id, get_stone, 1)  # todo
            pass
        # 检查通过，减少出售者物品，增加买家物品，减少买家灵石，增加卖家灵石
        sql_message.update_back_j(user_id, item_id, num=sell_item_num)
        sql_message.update_ls(user_id, get_stone, 1)
        item_type = items.items.get(item_id).get('goods_type')
        sql_message.send_back(want_user_id, item_id, item_name, item_type, sell_item_num, 1)
        msg = f"成功通过向灵宝楼向{want_user_name}道友出售了：\n{item_name}{sell_item_num}个\n获取了"

    # 获取总数据
    await bot.send(event, msg)
    await user_sell_to.finish()


@check_my_want_item.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def check_user_want_item_(
    bot: Bot,                     # 机器人实例
    event: GroupMessageEvent,     # 消息主体
    cmd: str = RawCommand(),      # 获取命令名称，用于标识翻页
    args: Message = CommandArg()  # 获取命令参数
):
    """
    查看自身求购物品
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    args_str = args.extract_plain_text()
    # 获取查看页数
    page = get_args_num(args_str, 2)
    page = page if page else 1
    # 获取总数据
    msg_list, items_map = user_store.check_user_want_all(user_id)
    # 翻页化数据
    msg_list = get_paged_msg(msg_list, page, cmd)
    await send_msg_handler(bot, event, msg_list)
    await check_my_want_item.finish()


@check_user_want_item.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def check_user_want_item_(
    bot: Bot,                     # 机器人实例
    event: GroupMessageEvent,     # 消息主体
    cmd: str = RawCommand(),      # 获取命令名称，用于标识翻页
    args: Message = CommandArg()  # 获取命令参数
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
    msg_list, items_map = user_store.check_user_want_all(look_user_id)
    # 翻页化数据
    msg_list = get_paged_msg(msg_list, page, cmd)
    await send_msg_handler(bot, event, msg_list)
    await check_user_want_item.finish()


@user_want_item.handle(parameterless=[Cooldown(at_sender=False)])
async def user_want_item_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """购物"""
    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    # 获取指令参数
    args_str = args.extract_plain_text()
    msg_strs = get_strs_from_str(args_str)
    item_name = msg_strs[0] if msg_strs else None
    item_id = items.get_item_id(item_name)
    if not item_id:
        msg = "物品不存在！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    item_info = items.items.get(item_id)
    item_rank = int(item_info["rank"])
    max_price_mul = max(3 * (item_rank - 100), 10)
    max_price = 1000000 + abs(item_rank - 55) * 100000 * max_price_mul
    min_price = 1000000 + abs(item_rank - 55) * 100000
    item_price = get_args_num(args_str, 1)
    if item_price > max_price:
        msg = "道友的求购价格未免太高了！！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    if item_price < min_price:
        msg = f"道友的求购价格未免太低了！！！\n{item_name}的价值至少为：{min_price}！！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    item_num = get_args_num(args_str, 2)
    want_dict = {"need_items_id": item_id, "need_items_price": item_price, "need_items_num": item_num}
    user_store.create_user_want(user_id, want_dict)
    item_num = item_num if item_num else "不限"
    msg = f"成功向本位面灵宝楼提交求购申请\n物品：{item_name}\n价格：{number_to(item_price)}|{item_price}灵石\n需求数量：{item_num}\n"
    await bot.send(event=event, message=msg)
    await user_want_item.finish()
