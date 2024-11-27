import random

from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent
)
from nonebot import on_command
import asyncio

from nonebot.typing import T_State
from ..xiuxian_limit.limit_database import limit_handle
from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_place import place
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, UserBuffDate
)
from ..xiuxian_utils.other_set import OtherSet
from ..xiuxian_config import XiuConfig, convert_rank
from ..xiuxian_utils.data_source import jsondata
from ..xiuxian_utils.utils import (
    number_to, check_user, check_user_type
)
from ..xiuxian_utils.clean_utils import get_strs_from_str, main_md
from ..xiuxian_utils.lay_out import Cooldown

sql_message = XiuxianDateManage()  # sql实例化至sql_massage

exp_up = on_command("修炼", aliases={"/修炼"}, priority=1, permission=GROUP, block=True)
power_break_up = on_command("吸收天地精华", aliases={"融合天地精华"}, priority=12, permission=GROUP, block=True)
power_break_up_help = on_command("天地精华", aliases={"天地精华帮助"}, priority=12, permission=GROUP, block=True)
world_rank_up = on_command("踏破虚空", aliases={"突破位面", "飞升"}, priority=12, permission=GROUP, block=True)
exp_up_end = on_command("结束修炼", aliases={"重置修炼状态", "停止修炼"}, priority=12, permission=GROUP, block=True)
all_end = on_command("重置状态", aliases={"重置闭关状态", "重置悬赏令状态"}, priority=12,
                     permission=GROUP, block=True)
active_gift = on_command("神州大地齐欢腾，祝福祖国永太平", priority=12, permission=GROUP, block=True)
hp_set = on_command("设置血量", priority=1, permission=GROUP, block=True)
hp_set_2 = on_command("设置血量2", priority=1, permission=GROUP, block=True)


@hp_set.handle(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def hp_set_(bot: Bot, event: GroupMessageEvent):
    """修炼"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    mp = user_info['mp']
    atk = user_info['atk']
    sql_message.update_user_attribute(user_id, 1000, mp, atk)
    msg = f"已将请求传递至数据库, 传递值hp:1000,mp:{mp},atk:{atk}"
    await bot.send(event=event, message=msg)
    await hp_set.finish()


@hp_set_2.handle(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def hp_set_2_(bot: Bot, event: GroupMessageEvent):
    """修炼"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    mp = user_info['mp']

    sql_message.update_user_hp_mp(user_id, 1000, mp)
    msg = f"已将请求传递至数据库, 传递值hp:1000,mp:{mp}"
    await bot.send(event=event, message=msg)
    await hp_set_2.finish()

@exp_up.handle(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def exp_up_(bot: Bot, event: GroupMessageEvent):
    """修炼"""

    user_type = 4  # 状态4为修炼中

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)
    if not is_type:
        if msg == "道友正在修炼中，请抱元守一，聚气凝神，勿要分心！\r若是调用修炼看到此消息，道友大概率需要：\r【停止修炼】！！！":
            pass
        else:
            await bot.send(event=event, message=msg)
            await exp_up.finish()
    sql_message.in_closing(user_id, user_type)  # 进入修炼状态
    exp_time = 6  # 闭关时长计算(分钟) = second // 60
    sleep_time = exp_time * 10
    msg = f"\r{user_info['user_name']}道友开始屏息凝神，感受道韵流动，进入{int(sleep_time)}秒修炼"
    await bot.send(event=event, message=msg)
    await asyncio.sleep(sleep_time)
    user_mes = sql_message.get_user_info_with_id(user_id)  # 获取用户信息
    level = user_mes['level']
    use_exp = user_mes['exp']
    main_hp_rank = jsondata.level_data()[user_mes['level']]["HP"]
    hp_speed = 25 * main_hp_rank
    mp_speed = 50

    max_exp = (
            int(OtherSet().set_closing_type(level)) * XiuConfig().closing_exp_upper_limit
    )  # 获取下个境界需要的修为 * 1.5为闭关上限
    user_get_exp_max = int(max_exp) - use_exp

    if user_get_exp_max < 0:
        # 校验当当前修为超出上限的问题，不可为负数
        user_get_exp_max = 0
    level_rate = sql_message.get_root_rate(user_mes['root_type'])  # 灵根倍率
    realm_rate = jsondata.level_data()[level]["spend"]  # 境界倍率
    user_buff_data = UserBuffDate(user_id)
    mainbuffdata = user_buff_data.get_user_main_buff_data()
    mainbuffratebuff = mainbuffdata['ratebuff'] if mainbuffdata is not None else 0  # 功法修炼倍率
    mainbuffclors = mainbuffdata['clo_rs'] if mainbuffdata is not None else 0  # 功法闭关回复
    place_id = place.get_now_place_id(user_id)
    world_id = place.get_world_id(place_id)
    world_buff = world_id * 0.3  # 位面灵气加成
    exp = int(
        (exp_time * XiuConfig().closing_exp) * (
            (level_rate * realm_rate * (1 + mainbuffratebuff)))
        # 洞天福地为加法
    )  # 本次闭关获取的修为
    user_type = 0  # 状态0为空闲中
    user_buff_data = UserBuffDate(user_id).BuffInfo
    exp = int(exp * (1 + user_buff_data['blessed_spot'] + world_buff))

    is_type, msg = check_user_type(user_id, 4)
    if not is_type:
        await exp_up.finish()
    if exp >= user_get_exp_max:
        # 用户获取的修为到达上限
        sql_message.in_closing(user_id, user_type)
        sql_message.update_exp(user_id, user_get_exp_max)
        sql_message.update_power2(user_id)  # 更新战力

        result_msg, result_hp_mp = OtherSet().send_hp_mp(user_id, int(exp * hp_speed * (1 + mainbuffclors)),
                                                         int(exp * mp_speed))
        sql_message.update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1], int(result_hp_mp[2] / 10))
        msg = f"\r{user_mes['user_name']}道友修炼结束，本次修炼触及瓶颈，共增加修为：{number_to(user_get_exp_max)}{result_msg[0]}{result_msg[1]}"
        msg = main_md(msg, '本次修炼耗时60s', '开始突破', '突破', '查看状态', '我的状态', '查看目前信息', '我的修仙信息', '修仙帮助', '修仙帮助')
        await bot.send(event=event, message=msg)
        await exp_up.finish()
    else:
        sql_message.in_closing(user_id, user_type)
        sql_message.update_exp(user_id, exp)
        sql_message.update_power2(user_id)  # 更新战力
        result_msg, result_hp_mp = OtherSet().send_hp_mp(user_id, int(exp * hp_speed * (1 + mainbuffclors)),
                                                         int(exp * mp_speed))
        sql_message.update_user_attribute(user_id, result_hp_mp[0], result_hp_mp[1], int(result_hp_mp[2] / 10))
        msg = f"\r{user_mes['user_name']}道友修炼结束，本次修炼增加修为：{number_to(exp)}{result_msg[0]}{result_msg[1]}"
        msg = main_md(msg, '本次修炼耗时60s', '继续修炼', '修炼', '查看状态', '我的状态', '查看目前信息', '我的修仙信息', '修仙帮助', '修仙帮助')
        await bot.send(event=event, message=msg)
        await exp_up.finish()


@exp_up_end.handle(parameterless=[Cooldown(cd_time=240, at_sender=False)])
async def exp_up_end_(bot: Bot, event: GroupMessageEvent):
    """退出修炼"""
    # 这里曾经是风控模块，但是已经不再需要了
    user_type = 0  # 状态为空闲

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 4)
    if is_type:
        sql_message.in_closing(user_id, user_type)  # 退出修炼状态
        msg = "道友收敛心神，停止了修炼。"
    else:
        msg = "道友现在没在修炼呢！！"
    await bot.send(event=event, message=msg)
    await exp_up_end.finish()


@all_end.handle(parameterless=[Cooldown(at_sender=False)])
async def all_end_(bot: Bot, event: GroupMessageEvent, state: T_State):
    """重置状态"""

    await bot.send(event=event, message="正在申请测试用重置状态，请在10秒内输入后台获取的代码")
    key = ""
    key_pre = "qwert-yuioppppp-asdffghjk-llzxcvb-nm12345-67890"
    for e in range(20):
        key += random.choice(key_pre)
    print(key)
    state["key"] = key


@all_end.receive()
async def all_end_(bot: Bot, event: GroupMessageEvent, state: T_State):
    """
    申请式重置状态
    :param bot:
    :param event:
    :param state:
    :return:
    """
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    input_key = event.get_plaintext().strip()
    user_id = user_info['user_id']

    if input_key == state["key"]:
        sql_message.in_closing(user_id, 0)  # 重置状态
        await bot.send(event=event, message="成功重置道友的状态！！！")
        await all_end.finish()
    else:
        msg = "密钥错误！！请不要随意调用调试接口！！！"
        await bot.send(event=event, message=msg)
        await all_end.finish()


@world_rank_up.handle(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def world_rank_up_(bot: Bot, event: GroupMessageEvent, state: T_State):
    """飞升上界"""
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)
    if not is_type:
        await bot.send(event=event, message=msg)
        await world_rank_up.finish()

    else:
        now_place = place.get_now_place_id(user_id)
        now_world = place.get_world_id(now_place)
        if now_world == 3:
            msg = "神域之上，谜团重重，敬请期待！"
            await bot.send(event=event, message=msg)
            await world_rank_up.finish()
        next_world = now_world + 1
        user_rank = convert_rank(user_info["level"])[0]
        next_world_name = place.get_world_id_name(next_world)
        now_world_name = place.get_world_id_name(now_world)
        need_level = XiuConfig().break_world_need[now_world]
        break_rank = convert_rank(need_level)[0]
        if user_rank >= break_rank:
            msg = (f"道友修为超凡，已然足矣踏破虚空离开【{now_world_name}】前往【{next_world_name}】"
                   f"\r注意：突破位面后将不可回到【{now_world_name}】，确认踏破虚空请回复我：确认飞升")
            state["world_up"] = next_world
            await bot.send(event=event, message=msg)
        else:
            msg = f"道友修为暂且不达离开【{now_world_name}】的最低要求{need_level}，还不足矣踏破虚空离开【{now_world_name}】!!!!"
            await bot.send(event=event, message=msg)
            await world_rank_up.finish()


@world_rank_up.receive(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def world_rank_up_(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 这里曾经是风控模块，但是已经不再需要了
    _, user_info, _ = check_user(event)

    user_name = user_info["user_name"]
    user_id = user_info["user_id"]
    next_world = state["world_up"]
    next_world_name = place.get_world_id_name(next_world)
    now_world_name = place.get_world_id_name(next_world - 1)
    arg = event.get_plaintext().strip()
    user_choice = get_strs_from_str(arg)[0]
    if user_choice == "确认飞升":
        next_place_all = place.get_world_place_list(next_world)
        next_place = random.choice(next_place_all)
        next_place_name = place.get_place_name(next_place)
        place.set_now_place_id(user_id, next_place)
        msg = f"恭喜大能{user_name}踏破虚空离开【{now_world_name}】，前往【{next_world_name}:{next_place_name}】！！！！"
    else:
        msg = "回答有误，取消飞升！！"
    await bot.send(event=event, message=msg)
    await world_rank_up.finish()


@power_break_up.handle(parameterless=[Cooldown(cd_time=2, at_sender=False)])
async def power_break_up_(bot: Bot, event: GroupMessageEvent):
    """利用天地精华"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    is_type, msg = check_user_type(user_id, 0)
    if is_type:
        power = limit_handle.get_user_world_power_data(user_id)
        if power == 0:
            msg = "道友体内没有天地精华！！！"
            await bot.send(event=event, message=msg)
            await power_break_up.finish()
        user_rank = convert_rank(user_info['level'])[0] + 1
        exp_time = power
        rate_up = power / user_rank if power / user_rank > 10 else 10
        level = user_info['level']
        level_rate = sql_message.get_root_rate(user_info['root_type'])  # 灵根倍率
        realm_rate = jsondata.level_data()[level]["spend"]  # 境界倍率
        user_buff_data = UserBuffDate(user_id)
        mainbuffdata = user_buff_data.get_user_main_buff_data()
        mainbuffratebuff = mainbuffdata['ratebuff'] if mainbuffdata is not None else 0  # 功法修炼倍率

        exp = int(
            (exp_time * XiuConfig().closing_exp) * (
                (level_rate * realm_rate * (1 + mainbuffratebuff)))
            # 洞天福地为加法
        )  # 本次闭关获取的修为
        exp = int(exp)

        sql_message.update_exp(user_id, exp)
        sql_message.update_power2(user_id)  # 更新战力
        leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
        sql_message.update_levelrate(user_id, leveluprate + 1 * rate_up)
        msg = f"道友成功将体内天地精华吸收，突破概率提升了{int(rate_up)}%, 修为提升了{number_to(exp)}|{exp}点！！"
        limit_handle.update_user_world_power_data(user_id, 0)
    else:
        pass
    await bot.send(event=event, message=msg)
    await power_break_up.finish()


@power_break_up_help.handle(parameterless=[Cooldown(cd_time=2, at_sender=False)])
async def power_break_up_help_(bot: Bot, event: GroupMessageEvent):
    """天地精华帮助"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    power = limit_handle.get_user_world_power_data(user_id)
    msg = (f"道友体内拥有天地精华：{power}\r天地精华由使用天地奇物获得\r可以发送 吸收天地精华 将体内天地精华吸收！！\r增加少许修为与突破概率"
           f"\r天地精华还是练就顶级神通的必备能量！！\r请尽快使用天地精华，否则天地精华将会归于天地之间！！！")
    await bot.send(event=event, message=msg)
    await power_break_up_help.finish()


@active_gift.handle(parameterless=[Cooldown(cd_time=60, at_sender=False)])
async def active_gift_(bot: Bot, event: GroupMessageEvent):
    """国庆福利"""

    _, user_info, _ = check_user(event)

    msg = f"国庆已经结束啦！！明年国庆再来吧！"
    await bot.send(event=event, message=msg)
    await active_gift.finish()



