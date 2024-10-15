from datetime import datetime

from .jsondata_move import save_move_data, Move, read_move_data
from ..xiuxian_config import convert_rank
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot import on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent
)
from nonebot.params import CommandArg
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage
)
from ..xiuxian_place import Place

from ..xiuxian_utils.utils import (
    check_user, check_user_type, get_num_from_str, get_strs_from_str
)

sql_message = XiuxianDateManage()

go_to = on_command("移动", aliases={"前往", "去"}, permission=GROUP, priority=10, block=True)
get_map = on_fullmatch("地图", permission=GROUP, priority=10, block=True)
complete_move = on_command("行动结算", aliases={"到达"}, permission=GROUP, priority=10, block=True)
stop_move = on_fullmatch("停止移动", permission=GROUP, priority=10, block=True)


@go_to.handle(parameterless=[Cooldown(at_sender=False)])
async def go_to_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """
    移动位置测试 到 位置id
    :param bot:
    :param event:
    :param args:
    :return: msg：distance
    """
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await get_map.finish()
    user_id = user_info['user_id']

    is_type, msg = check_user_type(user_id, 0)  # 需要空闲的用户
    if not is_type:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await complete_move.finish()
    msg_text = args.extract_plain_text()
    start_id = Place().get_now_place_id(user_id)
    num = get_num_from_str(msg_text)
    name = get_strs_from_str(msg_text)
    place_id = None
    if name:
        place_id = Place().get_place_id(name[0])
    if num:
        place_id = int(num[0])
    if place_id is None:
        msg = "请输入正确的地点或地点id！！！"
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await go_to.finish()
    far, name_1, name_2 = Place().get_distance(start_id, place_id)
    if far == "unachievable":
        msg = f"无法从【{name_1}】移动至【{name_2}】！！！目的地跨位面或不可到达"

    elif far == 0:
        msg = f"道友已在【{name_1}】！！"

    else:
        need_time = far / (convert_rank(user_info["level"])[0] + 60) * 60 * 10
        move_data = {
            "start_id": start_id,
            "to_id": place_id,
            "need_time": need_time
        }
        save_move_data(user_id, move_data)
        sql_message.do_work(user_id, -1, need_time)
        msg = f"道友开始从【{name_1}】移动至【{name_2}】, 距离约：{far:.1f}万里, 预计耗时{need_time:.1f}分钟！"

    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await go_to.finish()


@stop_move.handle(parameterless=[Cooldown(cd_time=30, at_sender=False)])
async def stop_move_(bot: Bot, event: GroupMessageEvent):
    """移动结算"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await stop_move.finish()

    user_id = user_info['user_id']

    is_type, msg = check_user_type(user_id, int(-1))  # 需要在移动中的用户
    if is_type:
        msg = "\n道友飞速赶回了出发点！！"
        sql_message.do_work(user_id, 0)
    else:
        pass
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await stop_move.finish()


@complete_move.handle(parameterless=[Cooldown(at_sender=False)])
async def complete_move_(bot: Bot, event: GroupMessageEvent):
    """移动结算"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await complete_move.finish()

    user_id = user_info['user_id']

    is_type, msg = check_user_type(user_id, int(-1))  # 需要在移动中的用户
    if not is_type:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await complete_move.finish()
    else:
        user_cd_message = sql_message.get_user_cd(user_id)
        work_time = datetime.strptime(
            user_cd_message['create_time'], "%Y-%m-%d %H:%M:%S.%f"
        )
        pass_time = (datetime.now() - work_time).seconds // 60  # 时长计算
        move_info = read_move_data(user_id)
        need_time = move_info["need_time"]
        place_name = Place().get_place_name(move_info["to_id"])
        if pass_time < need_time:
            msg = f"向【{place_name}】的移动，预计{need_time - pass_time:.1f}分钟后可结束"
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await complete_move.finish()
        else:  # 移动结算逻辑
            sql_message.do_work(user_id, 0)
            place_id = move_info["to_id"]
            Place().set_now_place_id(user_id, place_id)
            msg = f"道友雷厉风行，成功到达【{place_name}】！"
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await complete_move.finish()


@get_map.handle(parameterless=[Cooldown(at_sender=False)])
async def get_map_(bot: Bot, event: GroupMessageEvent):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await get_map.finish()
    user_id = user_info['user_id']
    user_cd_message = sql_message.get_user_cd(user_id)
    place_id = user_cd_message["place_id"]
    world_name = Place().get_world_name(place_id)
    world_id = Place().get_world_id(place_id)
    msg = f"\n————{world_name}地图————\n"
    place_dict = Place().get_place_dict()
    for get_place_id, place in place_dict.items():
        place_world_id = place[1][2]
        if place_world_id == world_id:
            if place_id == get_place_id:
                msg += f"地区ID:{get_place_id}【{place[0]}】位置:{place[1][:2]}<道友在这\n"

            else:
                msg += f"地区ID:{get_place_id}【{place[0]}】位置:{place[1][:2]}\n"
        else:
            pass
    msg += "——————————\ntips: 发送【前往】+【目的地ID】来进行移动哦"
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await get_map.finish()
