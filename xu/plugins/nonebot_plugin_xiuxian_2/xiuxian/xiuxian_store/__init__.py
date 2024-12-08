import asyncio
import time

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)

from .store_database import user_store
from .. import XiuConfig
from ..xiuxian_utils.clean_utils import get_args_num, get_paged_msg, number_to_msg, get_strs_from_str
from ..xiuxian_utils.lay_out import Cooldown, set_cmd_lock
from nonebot.params import CommandArg, RawCommand
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.utils import (
    check_user,
    send_msg_handler, get_id_from_str, number_to
)
from ..xiuxian_utils.xiuxian2_handle import sql_message

store_sell_lock = asyncio.Lock()
break_bind = []

check_user_want_item = on_command("灵宝楼求购查看", aliases={"查看灵宝楼求购", "个人摊位查看"}, priority=2, permission=GROUP, block=True)
user_sell_to = on_command("灵宝楼出售", aliases={"个人摊位出售", "灵宝楼寄售"}, priority=2, permission=GROUP, block=True)
user_want_item = on_command("灵宝楼求购", aliases={"个人摊位求购"}, priority=2, permission=GROUP, block=True)
check_my_want_item = on_command("我的灵宝楼求购", aliases={"我的摊位"}, priority=2, permission=GROUP, block=True)
user_want_funds = on_command("灵宝楼存灵石", aliases={"个人摊位存灵石", "摊位存灵石", "预备资金"}, priority=2, permission=GROUP, block=True)
user_funds_extract = on_command("灵宝楼取灵石", aliases={"个人摊位取灵石", "摊位取灵石", "取资金"}, priority=2, permission=GROUP, block=True)
remove_want_item = on_command("取消灵宝楼求购", aliases={"取消求购"}, priority=2, permission=GROUP, block=True)
fast_sell_items = on_command("灵宝楼快速出售", aliases={"个人摊位快速出售"}, priority=2, permission=GROUP, block=True)
bind_break = on_command("物品解绑", priority=2, permission=GROUP, block=True)


@bind_break.handle(
    parameterless=[
        Cooldown(
            cd_time=24000,
            at_sender=False,
            parallel_block=True)])
async def bind_break_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
):
    """
    物品解绑
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    if user_id in break_bind:
        msg = '道友已解绑过物品！！'
        await bot.send(event, msg)
        set_cmd_lock(user_id, 0)
        await bind_break.finish()
    break_bind.append(user_id)
    msg = '开始为道友解绑物品，请稍后.....'
    await bot.send(event, msg)
    for item_type in ["技能", "装备"]:
        user_backs = sql_message.get_back_goal_type_msg(user_id, item_type)  # list(back)
        if not user_backs:
            continue
        for back_item in user_backs:
            item_info = items.get_data_by_item_id(back_item['goods_id'])
            item_rank = item_info['rank']
            if item_rank == 1000:
                continue
            item_id = back_item['goods_id']
            sql_message.break_bind_item(user_id, item_id)
            set_cmd_lock(user_id, int(time.time()))
            await asyncio.sleep(0.5)
    msg = '道友的物品解绑完成啦！'
    await bot.send(event, msg)
    set_cmd_lock(user_id, 0)
    await bind_break.finish()


@fast_sell_items.handle(
    parameterless=[
        Cooldown(
            cd_time=30,
            at_sender=False,
            parallel_block=True)])
async def fast_sell_items_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
        args: Message = CommandArg()  # 获取命令参数
):
    """
    灵宝楼快速出售
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    strs = args.extract_plain_text()
    want_user_id = get_id_from_str(strs)
    if not want_user_id:
        msg = "请输正确的道号来快速向对应道友出售物品！！！"
        await bot.send(event=event, message=msg)
        set_cmd_lock(user_id, 0)
        await fast_sell_items.finish()
    if want_user_id == user_id:
        msg = "请不要向自己出售物品！！！"
        await bot.send(event=event, message=msg)
        set_cmd_lock(user_id, 0)
        await fast_sell_items.finish()
    args = get_strs_from_str(strs)
    want_user_name = args[0]
    args = args[1:]
    if args:
        the_same = XiuConfig().elixir_def
        real_args = [the_same[i] if i in the_same else i for i in args]
        sell_list = []
        for goal_level, goal_level_name in zip(real_args, args):
            back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
            for back in back_msg:
                goods_name = back['goods_name']
                goods_id = back['goods_id']
                goods_num = back['goods_num'] - back['bind_num']
                item_info = items.get_data_by_item_id(goods_id)
                buff_type = item_info.get('buff_type')
                item_level = item_info.get('level') if item_info else None
                item_type = back.get('goods_type')
                if (item_level == goal_level
                        or goods_name == goal_level
                        or buff_type == goal_level
                        or item_type == goal_level) and goods_num > 0:
                    sell_list.append(back)
        msg = f"开始向{want_user_name}道友快速出售以下类型物品：\r" + "|".join(args) + "请等待...."
        await bot.send(event, msg)
        msg = '出售结果如下'
    else:
        # 无参数
        sell_list = []
        msg = f"请指定你要向{want_user_name}道友出售的物品的类型！！"
        await bot.send(event, msg)
        set_cmd_lock(user_id, 0)
        await fast_sell_items.finish()
    sell_msg = []
    price_sum = 0
    want_pass = False
    funds_pass = True
    for item_in_back in sell_list:
        item_id = item_in_back['goods_id']
        item_name = item_in_back['goods_name']
        # 物品数量检查
        sell_item_num = item_in_back['goods_num'] - item_in_back['bind_num']
        if item_in_back['goods_type'] == "装备" and int(item_in_back['state']) == 1:
            continue
        want_item = user_store.check_user_want_item(want_user_id, item_id, 1)
        if not want_item:
            continue
        want_pass = True
        want_item_num = want_item['need_items_num']
        want_item_price = want_item['need_items_price']
        get_stone = want_item_price * sell_item_num
        if want_item_num:  # 有数量限制
            # 卖的太多啦！！！！人家收不下！
            if want_item_num < sell_item_num:
                msg += f"\r尝试出售【{item_name}】！！"
                continue
            if want_item_num == sell_item_num:
                # 卖完了
                user_store.store_data.del_want_item(want_user_id, item_id)
            else:
                user_store.update_user_want(user_info, sell_item_num, want_user_id, want_item)
        else:  # 无数量限制，检查资金是否充足
            want_item_funds = user_store.get_user_funds(want_user_id)  # 获取玩家摊位资金
            if get_stone > want_item_funds:  # 资金不足
                funds_pass = False
                continue
            user_store.update_user_funds(want_user_id, get_stone, 1)  # 减少资金
        # 检查通过，减少出售者物品，增加买家物品，减少买家资金储备，增加卖家灵石
        sql_message.update_back_j(user_id, item_id, num=sell_item_num)
        sql_message.update_ls(user_id, get_stone, 1)
        price_sum += get_stone
        item_type = items.items.get(str(item_id)).get('type')
        sql_message.send_back(want_user_id, item_id, item_name, item_type, sell_item_num, 0)
        sell_msg.append(f"【{item_name}】{sell_item_num}个 获取了{get_stone}灵石")
        set_cmd_lock(user_id, int(time.time()))
        await asyncio.sleep(0.5)
    if sell_msg:
        msg += f"\r成功向{want_user_name}道友出售了：\r" + '\r'.join(sell_msg) + f'\r总计: {number_to(price_sum)}灵石'
    elif not want_pass:
        msg += f"\r对方对道友的物品没有需求！"
    elif not funds_pass:
        msg += f"\r对方的资金不足！！！"
    else:
        msg += f"\r对方无法收下道友的全部物品！！"

    await bot.send(event, msg)
    set_cmd_lock(user_id, 0)
    await fast_sell_items.finish()


@user_want_funds.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def user_want_funds_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
        args: Message = CommandArg()  # 获取命令参数
):
    """
    灵宝楼存入灵石
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    funds_num = get_args_num(args, 1)
    if funds_num > user_info['stone']:
        msg = "道友的灵石不足！！！"
        await bot.send(event, msg)
        await user_want_funds.finish()
    sql_message.update_ls(user_id, funds_num, 2)  # 减少灵石
    user_funds = user_store.update_user_funds(user_id, funds_num, 0)  # 增加资金
    msg = f"道友成功在灵宝楼存入{number_to_msg(funds_num)}灵石作为资金。\r当前灵宝楼存有：{number_to_msg(user_funds)}灵石"
    await bot.send(event, msg)
    await user_want_funds.finish()


@remove_want_item.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def remove_want_item_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
        args: Message = CommandArg()  # 获取命令参数
):
    """
    下架自身求购物品
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    args_str = args.extract_plain_text()
    arg_strs = get_strs_from_str(args_str)
    item_name = arg_strs[0] if arg_strs else None
    item_id = items.items_map.get(item_name)
    want_item_info = user_store.check_user_want_item(user_id, item_id, 1)
    if not want_item_info:
        # 如果没有物品则驳回
        msg = f"道友没有此物品的求购！！！"
        await bot.send(event, msg)
        await remove_want_item.finish()
    user_store.store_data.del_want_item(user_id, item_id)
    back_stone = int(want_item_info['need_items_price'] * want_item_info['need_items_num'] * 0.8)
    sql_message.update_ls(user_id, back_stone, 1)  # 增加灵石
    msg = f"成功取消对{item_name}的求购。\r回退{number_to_msg(back_stone)}灵石"
    await bot.send(event, msg)
    await remove_want_item.finish()


@user_funds_extract.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def user_funds_extract_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
        args: Message = CommandArg()  # 获取命令参数
):
    """
    查看自身求购物品
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    funds_num = get_args_num(args, 1)
    user_funds = user_store.get_user_funds(user_id)  # 获取玩家摊位资金
    if funds_num > user_funds:
        msg = f"道友的灵宝楼内资金不足！！！\r当前灵宝楼内仅存有：{number_to_msg(user_funds)}灵石"
        await bot.send(event, msg)
        await user_funds_extract.finish()
    user_funds = user_store.update_user_funds(user_id, funds_num, 1)  # 减少资金
    stone_extract = int(funds_num * 0.8)
    stone_handle = funds_num * 0.2
    sql_message.update_ls(user_id, stone_extract, 1)  # 增加灵石
    msg = (f"道友成功自灵宝楼取出{number_to_msg(stone_extract)}灵石。\r"
           f"收取手续费{number_to_msg(stone_handle)}枚灵石。\r"
           f"当前灵宝楼存有：{number_to_msg(user_funds)}灵石")
    await bot.send(event, msg)
    await user_funds_extract.finish()


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
    async with store_sell_lock:
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
            msg = (f"道友的包内没有那么多可交易{item_name}！！！\r"
                   f"当前拥有：{item_in_back['goods_num']}个\r"
                   f"绑定数量：{item_in_back['bind_num']}个")
            await bot.send(event, msg)
            await user_sell_to.finish()
        if item_in_back['goods_type'] == "装备" and int(item_in_back['state']) == 1:
            msg = f"装备：{item_name}已经被道友装备在身，无法出售！！"
            await bot.send(event, msg)
            await user_sell_to.finish()
        # 指定用户出售判定（如果有）
        if len(arg_strs) > 1:
            want_user_name = arg_strs[1]
            want_user_id = sql_message.get_user_id(want_user_name)
            if not want_user_id:
                msg = f"修仙界中没有此人的踪迹！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
            if user_id == want_user_id:
                msg = f"请不要向自己出售物品！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
            want_item = user_store.check_user_want_item(want_user_id, item_id, 1)
            if not want_item:
                msg = f"{want_user_name}道友现在似乎对{item_name}不感兴趣！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
        else:  # 没有指定玩家
            want_item = user_store.check_highest_want_item(user_id, item_id, sell_item_num, 1)  # 获取物品售价最高玩家
            if not want_item:
                msg = f"现在似乎无人需要{sell_item_num}个{item_name}！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()

            want_user_id = want_item['user_id']
            want_user_info = sql_message.get_user_info_with_id(want_user_id)
            want_user_name = want_user_info['user_name']

        want_item_num = want_item['need_items_num']
        want_item_price = want_item['need_items_price']
        get_stone = want_item_price * sell_item_num
        if want_item_num:  # 有数量限制
            # 卖的太多啦！！！！人家收不下！
            if want_item_num < sell_item_num:
                msg = f"{want_user_name}道友仅需要{want_item_num}个{item_name}！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
            if want_item_num == sell_item_num:
                # 卖完了
                user_store.store_data.del_want_item(want_user_id, item_id)
            else:
                user_store.update_user_want(user_info, sell_item_num, want_user_id, want_item)
        else:  # 无数量限制，检查资金是否充足
            want_item_funds = user_store.get_user_funds(want_user_id)  # 获取玩家摊位资金
            if get_stone > want_item_funds:  # 资金不足
                msg = f"{want_user_name}道友的资金储备不足，无法收购如此多的{item_name}！！！！"
                await bot.send(event, msg)
                await user_sell_to.finish()
            user_store.update_user_funds(want_user_id, get_stone, 1)  # 减少资金
        # 检查通过，减少出售者物品，增加买家物品，减少买家资金储备，增加卖家灵石
        sql_message.update_back_j(user_id, item_id, num=sell_item_num)
        sql_message.update_ls(user_id, get_stone, 1)
        item_type = items.items.get(str(item_id)).get('type')
        sql_message.send_back(want_user_id, item_id, item_name, item_type, sell_item_num, 0)
        msg = f"成功通过向灵宝楼向{want_user_name}道友出售了：\r{item_name}{sell_item_num}个\r获取了{get_stone}灵石"

        await bot.send(event, msg)
        await user_sell_to.finish()


@check_my_want_item.handle(
    parameterless=[
        Cooldown(
            cd_time=10,
            at_sender=False)])
async def check_my_want_item_(
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
    page = get_args_num(args_str, 1)
    page = page if page else 1
    # 添加信息头，显示余额
    user_funds = user_store.get_user_funds(user_id)
    msg_head = f"当前灵宝楼存有{number_to_msg(user_funds)}灵石"
    # 获取总数据
    msg_list, items_map = user_store.check_user_want_all(user_id)
    # 翻页化数据
    msg_list = get_paged_msg(msg_list, page, cmd=cmd, msg_head=msg_head)
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
    查看求购物品
    """
    # 获取用户数据
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    # 提取命令详情
    args_str = args.extract_plain_text()
    # 获取查看页数
    page = get_args_num(args_str, 1)
    page = page if page else 1
    first_arg = a[0] if (a := get_strs_from_str(args_str)) else None

    if look_item_id := items.items_map.get(first_arg):  # 输入的首个名称为物品
        msg_list = [user_store.check_highest_want_item(user_id, look_item_id, sell_item_num=1)]
    elif look_user_id := get_id_from_str(args_str):  # 输入的首个名称为玩家
        # 获取总数据
        msg_list, items_map = user_store.check_user_want_all(look_user_id)
        # 翻页化数据
        msg_list = get_paged_msg(msg_list, page, cmd)
    else:
        msg_list = ["请输入正确的物品名或用户名！！！"]
    await send_msg_handler(bot, event, msg_list)
    await check_user_want_item.finish()


@user_want_item.handle(parameterless=[Cooldown(at_sender=False)])
async def user_want_item_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """物品求购"""
    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    user_stone = user_info['stone']
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
    max_price_mul = max(3 * (item_rank - 90), 10)
    max_price = 1000000 + abs(item_rank - 55) * 100000 * max_price_mul
    min_price = 1000000 + abs(item_rank - 55) * 100000
    item_price = get_args_num(args_str, 1)
    if item_price % 100000:
        msg = "求购价格必须为10w的整数倍！！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()

    if item_price > max_price:
        msg = "道友的求购价格未免太高了！！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    if item_price < min_price:
        msg = f"道友的求购价格未免太低了！！！\r{item_name}的价值至少为：{number_to(min_price)}|{min_price}！！！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    want_item = user_store.check_user_want_item(user_id, item_id, 1)
    if want_item:
        if want_item.get('need_items_num'):
            msg = f"道友已有此物的求购！！！\r若要更改，请先【取消求购{item_name}】!!!!"
            await bot.send(event=event, message=msg)
            await user_want_item.finish()

    item_num = get_args_num(args_str, 2)
    want_dict = {"need_items_id": item_id, "need_items_price": item_price, "need_items_num": item_num}
    if item_num:
        sum_price = item_price * item_num
        if sum_price > user_stone:
            msg = f"道友的灵石不足！！！\r当前仅有{number_to(user_stone)}|{user_stone}！！！"
            await bot.send(event=event, message=msg)
            await user_want_item.finish()
        sql_message.update_ls(user_id, sum_price, 2)
        funds_msg = f"消耗{number_to(sum_price)}|{sum_price}灵石"
    else:
        funds_msg = "请使用【灵宝楼存灵石】预存灵石来维持摊位运转"
        item_num = "不限"
    msg = f"成功向本位面灵宝楼提交求购申请\r物品：{item_name}\r价格：{number_to(item_price)}|{item_price}灵石\r需求数量：{item_num}\r{funds_msg}"
    user_store.create_user_want(user_id, want_dict)
    await bot.send(event=event, message=msg)
    await user_want_item.finish()
