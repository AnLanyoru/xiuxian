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
from ..xiuxian_place import Place
from ..xiuxian_utils.data_source import jsondata
from ..xiuxian_utils.lay_out import Cooldown, CooldownIsolateLevel
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from ..xiuxian_utils.item_json import items
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic,
    send_msg_handler, CommandObjectID,
    Txt2Img, number_to, get_strs_from_str, get_num_from_str
)
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, get_weapon_info_msg, get_armor_info_msg,
    get_sec_msg, get_main_info_msg, get_sub_info_msg, UserBuffDate
)
from ..xiuxian_config import XiuConfig, convert_rank


check_user_want_item = on_command("个人摊位查看", aliases={"查看个人摊位"}, priority=8, permission=GROUP, block=True)
user_sell_to = on_command("个人摊位出售", priority=8, permission=GROUP, block=True)
user_want_item = on_command("个人摊位求购", priority=8, permission=GROUP, block=True)


@check_user_want_item.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def check_user_want_item_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """坊市查看"""
    _, user_info, _ = check_user(event)
    user_id = user_info["user_id"]
    place_id = str(Place().get_now_place_id(user_id))
    data_list = []
    if shop_data[place_id] == {}:
        msg = "此地的坊市目前空空如也！"
        await bot.send(event=event, message=msg)
        await check_user_want_item.finish()
    page = get_num_from_str(args.extract_plain_text())
    for k, v in shop_data[place_id].items():
        msg = f"编号：{k}\n"
        msg += f"{v['desc']}"
        msg += f"\n价格：{v['price']}枚灵石\n"
        if v['user_id'] != 0:
            msg += f"拥有人：{v['user_name']}道友\n"
            msg += f"数量：{v['stock']}\n"
        else:
            msg += f"百宝楼寄售\n"
        data_list.append(msg)
    items_all = len(data_list)
    page_all = ((items_all // 12) + 1) if (items_all % 12 != 0) else (items_all // 12)  # 总页数
    if page:
        page = page[0]
        pass
    else:
        page = 1
    page = int(page)
    if page_all < page:
        msg = "此地坊市没有那么多东西！！！"
        await bot.send(event=event, message=msg)
        await check_user_want_item.finish()
    items_start = page * 12 - 12
    items_end = items_start + 12
    data_list = data_list[items_start:items_end]
    page_info = f"第{page}/{page_all}页\n———tips———\n可以发送 查看坊市 页数 来查看更多商品哦"
    data_list.append(page_info)
    await send_msg_handler(bot, event, '坊市', bot.self_id, data_list)
    await check_user_want_item.finish()


@user_want_item.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def buy_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """购物"""
    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    place_id = str(Place().get_now_place_id(user_id))
    shop_data = user_want_item(place_id)

    if shop_data[place_id] == {}:
        msg = "此地的坊市目前空空如也！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    input_args = args.extract_plain_text().strip().split()
    if len(input_args) < 1:
        # 没有输入任何参数
        msg = "请输入正确指令！例如：坊市购买 物品编号 数量"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    else:
        try:
            arg = int(input_args[0])
            if len(input_args) == 0:
                msg = "请输入正确指令！例如：坊市购买 物品编号 数量"

            goods_info = shop_data[place_id].get(str(arg))
            if not goods_info:
                raise ValueError("编号对应的商品不存在！")

            purchase_quantity = int(input_args[1]) if len(input_args) > 1 else 1
            if purchase_quantity <= 0:
                raise ValueError("购买数量必须是正数！")

            if 'stock' in goods_info and purchase_quantity > goods_info['stock']:
                raise ValueError("购买数量超过库存限制！")
        except ValueError as e:
            msg = f"请输入正确的物品编号而不是物品名称！！！"
            await bot.send(event=event, message=msg)
            await user_want_item.finish()
    shop_user_id = shop_data[place_id][str(arg)]['user_id']
    goods_price = goods_info['price'] * purchase_quantity
    goods_stock = goods_info.get('stock', 1)
    if user_info['stone'] < goods_price:
        msg = '没钱还敢来买东西！！'
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    elif int(user_id) == int(shop_data[place_id][str(arg)]['user_id']):
        msg = "道友自己的东西就不要自己购买啦！"
        await bot.send(event=event, message=msg)
        await user_want_item.finish()
    elif purchase_quantity > goods_stock and shop_user_id != 0:
        msg = "库存不足，无法购买所需数量！"
        await bot.send(event=event, message=msg)
    else:
        shop_goods_name = shop_data[place_id][str(arg)]['goods_name']
        shop_user_name = shop_data[place_id][str(arg)]['user_name']
        shop_goods_id = shop_data[place_id][str(arg)]['goods_id']
        shop_goods_type = shop_data[place_id][str(arg)]['goods_type']
        sql_message.update_ls(user_id, goods_price, 2)
        sql_message.send_back(user_id, shop_goods_id, shop_goods_name, shop_goods_type, purchase_quantity)
        save_shop(shop_data)

        if shop_user_id == 0:  # 0为系统
            msg = f"{user_name}道友成功购买{purchase_quantity}个{shop_goods_name}，消耗灵石{goods_price}枚！"
        else:
            goods_info['stock'] -= purchase_quantity
            if goods_info['stock'] <= 0:
                del shop_data[place_id][str(arg)]  # 库存为0，移除物品
            else:
                shop_data[place_id][str(arg)] = goods_info
            service_charge = int(goods_price * 0.1)  # 手续费10%
            give_stone = goods_price - service_charge
            msg = f"{user_name}道友成功购买{purchase_quantity}个{shop_user_name}道友寄售的{shop_goods_name}，消耗灵石{goods_price}枚,坊市收取手续费：{service_charge}枚灵石！"
            sql_message.update_ls(shop_user_id, give_stone, 1)
        shop_data[place_id] = reset_dict_num(shop_data[place_id])
        save_shop(shop_data)
        LimitHandle().update_user_shop_log_data(user_id, msg)
        LimitHandle().update_user_shop_log_data(shop_user_id, msg)
        await bot.send(event=event, message=msg)
        await buy.finish()

