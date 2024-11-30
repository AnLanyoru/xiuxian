import operator

from nonebot.params import CommandArg
from .tower_database import tower_handle
from .tower_fight import get_tower_battle_info
from ..xiuxian_place import place
from ..xiuxian_sect import get_config
from ..xiuxian_utils.clean_utils import msg_handler, main_md
from ..xiuxian_utils.utils import check_user, check_user_type, send_msg_handler
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, sql_message
)
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    Message,
    PRIVATE
)
from ..xiuxian_utils.lay_out import Cooldown


tower_rule = on_command("挑战之地规则详情", aliases={"挑战之地规则"}, priority=2, permission=GROUP | PRIVATE, block=True)
tower_start = on_command("进入挑战之地", aliases={"进入挑战"}, priority=2, permission=GROUP | PRIVATE, block=True)
tower_end = on_command("离开挑战之地", aliases={"离开挑战"}, priority=2, permission=GROUP | PRIVATE, block=True)
tower_info = on_command("查看挑战", aliases={"查看挑战信息"}, priority=1, permission=GROUP | PRIVATE, block=True)
tower_fight = on_command("开始挑战", aliases={"挑战开始"}, priority=3, permission=GROUP | PRIVATE, block=True)
tower_shop = on_command("挑战商店", priority=3, permission=GROUP | PRIVATE, block=True)
tower_shop_buy = on_command("挑战商店兑换", aliases={"挑战积分兑换", "挑战兑换"}, priority=3, permission=GROUP | PRIVATE, block=True)
tower_point_get = on_command("挑战积分结算",aliases={"结算挑战积分"}, priority=3, permission=GROUP | PRIVATE, block=True)
tower_point_get_check = on_command("确认结算挑战积分", priority=3, permission=GROUP | PRIVATE, block=True)

@tower_point_get.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_point_get_(bot: Bot, event: GroupMessageEvent):
    """离开挑战之地"""

    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    user_tower_info = tower_handle.check_user_tower_info(user_id)
    if not user_tower_info:
        msg = '没有道友的挑战信息！！'
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()

    had_get = user_tower_info.get('weekly_point')
    if had_get == -1:
        msg = '道友本周已经领取过挑战积分啦！！'
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()
    else:
        best_floor = had_get
        place_id = user_tower_info.get('tower_place')
        world_id = place.get_world_id(place_id)
        tower = tower_handle.tower_data.get(world_id)
        point_get = tower.point_give.get(had_get)
        msg = f"请先确认你的积分领取！！"
        text =  f"！本次周最深抵达第{best_floor}区域，将可获取{point_get}积分！！"
        msg = main_md(
            msg, text,
            '确认领取', '确认结算挑战积分',
            '挑战商店', '挑战商店',
            '积分规则详情', '挑战之地规则详情',
            '挑战帮助', '挑战帮助')
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()

@tower_point_get.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_point_get_(bot: Bot, event: GroupMessageEvent):
    """离开挑战之地"""

    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    user_tower_info = tower_handle.check_user_tower_info(user_id)
    if not user_tower_info:
        msg = '没有道友的挑战信息！！'
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()

    had_get = user_tower_info.get('weekly_point')
    if had_get == -1:
        msg = '道友本周已经领取过挑战积分啦！！'
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()
    else:
        user_tower_info['weekly_point'] = -1
        place_id = user_tower_info.get('tower_place')
        world_id = place.get_world_id(place_id)
        tower = tower_handle.tower_data.get(world_id)
        point_get = tower.point_give.get(had_get)
        tower_handle.update_user_tower_point(user_id, point_get)
        tower_handle.update_user_tower_info(user_id, user_tower_info)
        msg = f"领取挑战积分成功！！！"
        text =  f"本次周最深抵达第{had_get}区域，累计获取{point_get}积分！！"
        msg = main_md(
            msg, text,
            '进入挑战', '进入挑战',
            '挑战商店', '挑战商店',
            '积分规则详情', '挑战之地规则详情',
            '挑战帮助', '挑战帮助')
        await bot.send(event=event, message=msg)
        await tower_point_get.finish()

@tower_rule.handle(
    parameterless=[
        Cooldown(
            cd_time=3,
            at_sender=False)])
async def tower_rule_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
):
    msg = ("- 挑战之地规则详情 -\r"
           "进入挑战之地后，无法进行修炼。\r"
           "挑战之地积分在进入新的挑战之地后，如变更挑战之地，将会清空原有积分。\r"
           "如：灵虚古境挑战者飞升后进入紫霄神渊，将清空积分\r"
           "挑战层层连续进行，中途退出将直接结算本次挑战，记录最高抵达层数\r"
           "重新开始挑战将自最高层数记录的一半开始挑战\r"
           "每周天八点重置结算挑战积分次数")
    await bot.send(event, msg)
    await tower_rule.finish()


@tower_shop.handle(
    parameterless=[
        Cooldown(
            cd_time=3,
            at_sender=False)])
async def tower_shop_(
        bot: Bot,                     # 机器人实例
        event: GroupMessageEvent,     # 消息主体
):
    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    shop_msg, msg = tower_handle.get_tower_shop_info(user_id)
    if not shop_msg:
        msg = "道友还未参加过位面挑战！"
        await bot.send(event=event, message=msg)
        await tower_fight.finish()
    text = msg_handler(bot, event, shop_msg)
    msg = main_md(
        msg, text,
        '挑战积分兑换 物品编号', '挑战积分兑换',
        '结算本周积分', '挑战积分结算',
        '积分规则详情', '挑战之地规则详情',
        '挑战帮助', '挑战帮助')
    await bot.send(event=event, message=msg)
    await tower_shop.finish()


@tower_fight.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_fight_(bot: Bot, event: GroupMessageEvent):
    """进行挑战"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 6)  # 需要挑战中的用户
    if not is_type:
        await bot.send(event=event, message=msg)
        await tower_fight.finish()
    user_tower_info = tower_handle.check_user_tower_info(user_id)
    floor = user_tower_info['now_floor']
    place_id = user_tower_info.get('tower_place')
    world_id = place.get_world_id(place_id)
    next_floor = floor + 1
    tower_floor_info = tower_handle.get_tower_floor_info(next_floor, place_id)
    if not tower_floor_info:
        best_floor = user_tower_info['now_floor']
        user_tower_info['now_floor'] = 0
        user_tower_info['best_floor'] = best_floor
        tower_handle.update_user_tower_info(user_info, user_tower_info)
        sql_message.do_work(user_id, 0)
        msg = (f"道友已抵达【{tower_handle.tower_data[world_id].name}】之底！！！"
               f"本次成绩已记录！！")
        await bot.send(event=event, message=msg)
        await tower_fight.finish()
    result, victor = await get_tower_battle_info(user_info, tower_floor_info, bot.self_id)
    if victor == "群友赢了":  # 获胜
        user_tower_info['now_floor'] += 1
        tower_handle.update_user_tower_info(user_info, user_tower_info)
        msg = (f"道友成功战胜 {tower_floor_info['name']} "
               f"到达【{tower_handle.tower_data[world_id].name}】第{user_tower_info['now_floor']}区域！！！")
    else:  # 输了
        final_floor = user_tower_info['now_floor']
        best_floor = max(final_floor, user_tower_info['best_floor'])
        week_best = max(user_tower_info['now_floor'], user_tower_info['weekly_point'])
        user_tower_info['weekly_point'] = week_best
        user_tower_info['now_floor'] = 0
        user_tower_info['best_floor'] = best_floor
        tower_handle.update_user_tower_info(user_info, user_tower_info)
        sql_message.do_work(user_id, 0)
        msg = (f"道友不敌 {tower_floor_info['name']} 退出位面挑战【{tower_handle.tower_data[world_id].name}】！\r"
               f"本次抵达第{final_floor}区域，本周最深抵达第{week_best}区域，历史最深抵达第{best_floor}区域，已记录！！")
    text = msg_handler(result)
    msg = main_md(
        msg, text,
        '继续挑战', '开始挑战',
        '查看下层', '查看挑战',
        '终止挑战', '离开挑战',
        '挑战帮助', '挑战帮助')
    await bot.send(event=event, message=msg)
    await tower_fight.finish()


@tower_start.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_start_(bot: Bot, event: GroupMessageEvent):
    """进入挑战之地"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)  # 需要无状态的用户
    if not is_type:
        await bot.send(event=event, message=msg)
        await tower_start.finish()
    else:
        place_id = user_info.get('place_id')
        world_id = place.get_world_id(place_id)
        world_name = place.get_world_name(place_id)
        try:
            tower_handle.tower_data[world_id]
        except KeyError:
            msg = f'道友所在位面【{world_name}】尚未有位面挑战，敬请期待!'
            await bot.send(event=event, message=msg)
            await tower_start.finish()
        if place_id == (tower_place := tower_handle.tower_data[world_id].place):
            user_tower_info = tower_handle.check_user_tower_info(user_id)
            old_tower_place = user_tower_info['tower_place']
            if not operator.eq(old_tower_place, tower_place):
                user_tower_info['tower_place'] = tower_place
                user_tower_info['tower_point'] = 0
                user_tower_info['best_floor'] = 0
            user_tower_info['now_floor'] = int(operator.floordiv(user_tower_info['best_floor'], 2))
            msg = f"道友进入位面挑战【{tower_handle.tower_data[world_id].name}】！"
            text = "使用 查看挑战 来查看当前挑战信息！"
            sql_message.do_work(user_id, 6)
            tower_handle.update_user_tower_info(user_info, user_tower_info)
            msg = main_md(
                msg, text,
                '开始挑战', '开始挑战',
                '查看挑战', '查看挑战',
                '终止挑战', '离开挑战',
                '挑战帮助', '挑战帮助')
            await bot.send(event=event, message=msg)
            await tower_start.finish()
        else:
            far, start_place, to_place = place.get_distance(place_id, tower_handle.tower_data[world_id].place)
            msg = f"\r道友所在位置没有位面挑战!!\r"
            text = (f"当前位面【{world_name}】的位面挑战【{tower_handle.tower_data[world_id].name}】在距你{far:.1f}万里的：【{to_place}】\r"
                   f"可以发送【前往 {to_place}】来前去位面挑战所在位置挑战！")
            msg = main_md(
                msg, text,
                f'前往 {to_place}', f'前往 {to_place}',
                '进入挑战', '进入挑战',
                '挑战商店', '挑战商店',
                '挑战帮助', '挑战帮助')
            await bot.send(event=event, message=msg)
            await tower_start.finish()


@tower_info.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_info_(bot: Bot, event: GroupMessageEvent):
    """查看挑战"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 6)  # 需要挑战中的用户
    if not is_type:
        await bot.send(event=event, message=msg)
        await tower_info.finish()
    else:
        msg, text = tower_handle.get_user_tower_msg(user_info)
        msg = main_md(
            msg, text,
            '开始挑战', '开始挑战',
            '挑战商店', '挑战商店',
            '终止挑战', '离开挑战',
            '挑战帮助', '挑战帮助')
        await bot.send(event=event, message=msg)
        await tower_info.finish()


@tower_end.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_end_(bot: Bot, event: GroupMessageEvent):
    """离开挑战之地"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 6)  # 需要挑战中的用户
    if not is_type:
        await bot.send(event=event, message=msg)
        await tower_end.finish()
    else:
        user_tower_info = tower_handle.check_user_tower_info(user_id)
        place_id = user_tower_info.get('tower_place')
        world_id = place.get_world_id(place_id)
        week_best = max(user_tower_info['now_floor'], user_tower_info['weekly_point'])
        user_tower_info['weekly_point'] = week_best
        final_floor = user_tower_info['now_floor']
        best_floor = max(final_floor, user_tower_info['best_floor'])
        user_tower_info['best_floor'] = best_floor
        tower_handle.update_user_tower_info(user_info, user_tower_info)
        sql_message.do_work(user_id, 0)
        msg = f"道友成功退出位面挑战【{tower_handle.tower_data[world_id].name}】"
        text =  f"！本次抵达第{best_floor}区域\r本周最深抵达第{week_best}区域\r历史最深抵达第{best_floor}区域，已记录！！"
        msg = main_md(
            msg, text,
            '再次挑战', '进入挑战',
            '挑战商店', '挑战商店',
            '积分结算', '挑战积分结算',
            '挑战帮助', '挑战帮助')
        await bot.send(event=event, message=msg)
        await tower_end.finish()

