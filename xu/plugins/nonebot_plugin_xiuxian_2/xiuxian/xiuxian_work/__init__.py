import math
import os
from typing import Any, Tuple
from nonebot import on_regex, require, on_command
from nonebot.params import RegexGroup

from ..xiuxian_limit import limit_handle
from ..xiuxian_move import read_move_data
from xu.plugins.nonebot_plugin_xiuxian_2.xiuxian.xiuxian_place import place
from ..xiuxian_utils.clean_utils import get_datetime_from_str, get_num_from_str
from ..xiuxian_utils.lay_out import Cooldown
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent
)
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.other_set import OtherSet
from .work_handle import workhandle
from datetime import datetime
from ..xiuxian_utils.xiuxian_opertion import do_is_work
from ..xiuxian_utils.utils import check_user, check_user_type
from .reward_data_source import PLAYERSDATA
from ..xiuxian_utils.item_json import items
from ..xiuxian_config import convert_rank, XiuConfig

# 定时任务
resetrefreshnum = require("nonebot_plugin_apscheduler").scheduler
work = {}  # 悬赏令信息记录
sql_message = XiuxianDateManage()  # sql类
count = 6  # 免费次数

# 重置悬赏令刷新次数（已改被动）
# @resetrefreshnum.scheduled_job("cron", hour=3, minute=0)
# async def resetrefreshnum_():
#    sql_message.reset_work_num()
#    logger.opt(colors=True).info(f"<green>用户悬赏令刷新次数重置成功</green>")


last_work = on_command("最后的悬赏令", priority=15, block=True)
do_work = on_regex(
    r"^悬赏令(刷新|终止|结算|接取|帮助)?(\d+)?",
    priority=10,
    permission=GROUP,
    block=True
)
__work_help__ = f"""
悬赏令帮助信息:
指令：
1、悬赏令:获取对应实力的悬赏令
2、悬赏令刷新:刷新当前悬赏令,每日{count}次
实力支持：求道者~羽化境
3、悬赏令终止:终止当前悬赏令任务
4、悬赏令结算:结算悬赏奖励
5、悬赏令接取+编号：接取对应的悬赏令
6、最后的悬赏令:用于接了悬赏令却境界突破导致卡住的道友使用
""".strip()


@last_work.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def last_work_(bot: Bot, event: GroupMessageEvent):

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    user_level = user_info['level']
    user_rank = convert_rank(user_level)[0]
    is_type, msg = check_user_type(user_id, 2)  # 需要在悬赏令中的用户
    if (is_type and user_rank >= 11) or (
            is_type and user_info['exp'] >= sql_message.get_level_power("羽化境后期")) or (
            is_type and int(user_info['exp']) >= int(OtherSet().set_closing_type(user_level))
            * XiuConfig().closing_exp_upper_limit
    ):
        user_cd_message = sql_message.get_user_cd(user_id)
        work_time = datetime.strptime(
            user_cd_message['create_time'], "%Y-%m-%d %H:%M:%S.%f"
        )
        exp_time = (datetime.now() - work_time).seconds // 60  # 时长计算
        time2 = workhandle().do_work(
            # key=1, name=user_cd_message.scheduled_time  修改点
            key=1, name=user_cd_message['scheduled_time'], level=user_level, exp=user_info['exp'],
            user_id=user_info['user_id']
        )
        if exp_time < time2:
            msg = f"进行中的悬赏令【{user_cd_message['scheduled_time']}】，预计{time2 - exp_time}分钟后可结束"
            await bot.send(event=event, message=msg)
            await last_work.finish()
        else:
            msg, give_stone, s_o_f, item_id, big_suc = workhandle().do_work(
                2,
                work_list=user_cd_message['scheduled_time'],
                level=user_level,
                exp=user_info['exp'],
                user_id=user_info['user_id']
            )
            item_flag = False
            item_msg = None
            item_info = None
            if item_id != 0:
                item_flag = True
                item_info = items.get_data_by_item_id(item_id)
                item_msg = f"{item_info['level']}:{item_info['name']}"
            if big_suc:  # 大成功
                sql_message.update_ls(user_id, give_stone * 2, 1)
                sql_message.do_work(user_id, 0)
                msg = f"悬赏令结算，{msg}获得报酬{give_stone * 2}枚灵石"
                # todo 战利品结算sql
                if item_flag:
                    sql_message.send_back(user_id, item_id, item_info['name'], item_info['type'], 1)
                    msg += f"，额外获得奖励：{item_msg}!"
                else:
                    msg += "!"
                await bot.send(event=event, message=msg)
                await last_work.finish()

            else:
                sql_message.update_ls(user_id, give_stone, 1)
                sql_message.do_work(user_id, 0)
                msg = f"悬赏令结算，{msg}获得报酬{give_stone}枚灵石"
                if s_o_f:  # 普通成功
                    if item_flag:
                        sql_message.send_back(user_id, item_id, item_info['name'], item_info['type'], 1)
                        msg += f"，额外获得奖励：{item_msg}!"
                    else:
                        msg += "!"
                    await bot.send(event=event, message=msg)
                    await last_work.finish()

                else:  # 失败
                    msg += "!"
                    await bot.send(event=event, message=msg)
                    await last_work.finish()
    else:
        msg = "不满足使用条件！"
        await bot.send(event=event, message=msg)
        await last_work.finish()


@do_work.handle(parameterless=[Cooldown(cd_time=6, stamina_cost=0, at_sender=False)])
async def do_work_(bot: Bot, event: GroupMessageEvent, args: Tuple[Any, ...] = RegexGroup()):

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    sql_message.update_last_check_info_time(user_id)  # 更新查看修仙信息时间
    user_cd_info = sql_message.get_user_cd(user_id)
    if not os.path.exists(PLAYERSDATA / str(user_id) / "workinfo.json") and user_cd_info['type'] == 2:
        sql_message.do_work(user_id, 0)
        msg = "悬赏令已更新，已重置道友的状态！"
        await bot.send(event=event, message=msg)
        await do_work.finish()
    mode = args[0]  # 刷新、终止、结算、接取
    user_level = user_info['level']
    if int(user_info['exp']) >= int(OtherSet().set_closing_type(user_level)) * XiuConfig().closing_exp_upper_limit:
        # 获取下个境界需要的修为 * 1.5为闭关上限
        msg = "道友的修为已经到达上限，悬赏令已无法再获得经验！"
        await bot.send(event=event, message=msg)
        await do_work.finish()
    user_type = user_cd_info['type']
    if user_type and user_type != 2:
        msg_map = {1: "已经在闭关中，请输入【出关】结束后才能获取悬赏令！",
                   3: "道友在秘境中，请等待结束后才能获取悬赏令！",
                   4: "道友还在修炼中，请等待结束后才能获取悬赏令！",
                   5: "道友还在虚神界修炼中，请等待结束后才能获取悬赏令！"
                   }
        msg = msg_map.get(user_type)
        if not msg:
            # 赶路检测
            user_cd_info = sql_message.get_user_cd(user_id)
            work_time = datetime.strptime(
                user_cd_info['create_time'], "%Y-%m-%d %H:%M:%S.%f"
            )
            pass_time = (datetime.now() - work_time).seconds // 60  # 时长计算
            move_info = read_move_data(user_id)
            need_time = move_info["need_time"]
            place_name = place.get_place_name(move_info["to_id"])
            if pass_time < need_time:
                last_time = math.ceil(need_time - pass_time)
                msg = f"道友现在正在赶往【{place_name}】中！预计还有{last_time}分钟到达目的地！！"
            else:  # 移动结算逻辑
                sql_message.do_work(user_id, 0)
                place_id = move_info["to_id"]
                place.set_now_place_id(user_id, place_id)
        await bot.send(event=event, message=msg)
        await do_work.finish()

    if mode is None:  # 接取逻辑
        if (user_cd_info['scheduled_time'] is None) or (user_cd_info['type'] == 0):
            try:
                msg = work[user_id].msg + "\r——————————————\r使用 悬赏令接取【序号】 接取对应悬赏令！"
            except KeyError:
                msg = "没有查到你的悬赏令信息呢，请刷新！"
        elif user_cd_info['type'] == 2:
            work_time = datetime.strptime(
                user_cd_info['create_time'], "%Y-%m-%d %H:%M:%S.%f"
            )
            exp_time = (datetime.now() - work_time).seconds // 60  # 时长计算
            time2 = workhandle().do_work(key=1, name=user_cd_info['scheduled_time'], user_id=user_info['user_id'])
            if exp_time < time2:
                msg = f"进行中的悬赏令【{user_cd_info['scheduled_time']}】，预计{time2 - exp_time}分钟后可结束"
            else:
                msg = f"进行中的悬赏令【{user_cd_info['scheduled_time']}】，已结束，请输入【悬赏令结算】结算任务信息！"
        else:
            msg = "没有查到你的悬赏令信息呢，请刷新！"
        await bot.send(event=event, message=msg)
        await do_work.finish()

    if mode == "刷新":  # 刷新逻辑
        if user_cd_info['type'] == 2:
            work_time = datetime.strptime(
                user_cd_info['create_time'], "%Y-%m-%d %H:%M:%S.%f"
            )
            exp_time = (datetime.now() - work_time).seconds // 60
            time2 = workhandle().do_work(key=1, name=user_cd_info['scheduled_time'], user_id=user_info['user_id'])
            if exp_time < time2:
                msg = f"进行中的悬赏令【{user_cd_info['scheduled_time']}】，预计{time2 - exp_time}分钟后可结束"
            else:
                msg = f"进行中的悬赏令【{user_cd_info['scheduled_time']}】，已结束，请输入【悬赏令结算】结算任务信息！"
            await bot.send(event=event, message=msg)
            await do_work.finish()
        usernums = sql_message.get_work_num(user_id)

        is_user, user_info, msg = check_user(event)
        if not is_user:
            await bot.send(event=event, message=msg)
            await do_work.finish()

        freenum = count - usernums - 1
        item_use = False
        goods_num = 0
        if freenum < 0:
            freenum = 0
            back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
            # 这里扣道具
            goods_id = 640001
            for back in back_msg:
                if goods_id == back['goods_id']:
                    goods_num = back['goods_num']
                    break
            if goods_num > 0:
                item_use = True
                num = 1
                sql_message.update_back_j(user_id, goods_id, num=num)
                pass
            else:
                msg = f"道友今日的悬赏令次数已然用尽！！"
                await bot.send(event=event, message=msg)
                await do_work.finish()

        work_msg = workhandle().do_work(0, level=user_level, exp=user_info['exp'], user_id=user_id)
        n = 1
        work_list = []
        work_msg_f = f"☆------道友的个人悬赏令------☆\r"
        for i in work_msg:
            work_list.append([i[0], i[3]])
            work_msg_f += f"{n}、{get_work_msg(i)}"
            n += 1
        work_msg_f += f"(悬赏令每日次数：{count}, 今日余剩新次数：{freenum}次)"
        if item_use:
            work_msg_f += f"\r道友消耗悬赏衙牌一枚，成功刷新悬赏令，余剩衙牌{goods_num - 1}枚。"
        else:
            sql_message.update_work_num(user_id, usernums + 1)
        work[user_id] = do_is_work(user_id)
        work[user_id].msg = work_msg_f
        work[user_id].world = work_list
        msg = work[user_id].msg + "\r——————————————\r在10秒内直接回复我需要接取的悬赏令序号快速接取对应悬赏令！"
        await bot.send(event=event, message=msg)

    elif mode == "终止":
        is_type, msg = check_user_type(user_id, 2)  # 需要在悬赏令中的用户
        if is_type:
            sql_message.do_work(user_id, 0)
            msg = f"悬赏令已终止！"
        else:
            msg = "没有查到你的悬赏令信息呢，请刷新！"
        await bot.send(event=event, message=msg)
        await do_work.finish()

    elif mode == "结算":
        is_type, msg = check_user_type(user_id, 2)  # 需要在悬赏令中的用户
        if is_type:
            user_cd_info = sql_message.get_user_cd(user_id)
            work_time = get_datetime_from_str(user_cd_info['create_time'])
            exp_time = (datetime.now() - work_time).seconds // 60  # 时长计算
            time2 = workhandle().do_work(
                key=1, name=user_cd_info['scheduled_time'], level=user_level, exp=user_info['exp'],
                user_id=user_info['user_id']
            )
            time2 = 0
            if exp_time < time2:
                msg = f"进行中的悬赏令【{user_cd_info['scheduled_time']}】，预计{time2 - exp_time}分钟后可结束"
                await bot.send(event=event, message=msg)
                await do_work.finish()
            else:
                msg, give_exp, s_o_f, item_id, big_suc = workhandle().do_work(2,
                                                                              work_list=user_cd_info['scheduled_time'],
                                                                              level=user_level,
                                                                              exp=user_info['exp'],
                                                                              user_id=user_info['user_id'])
                item_flag = False
                item_info = None
                item_msg = None
                if item_id != 0:
                    item_flag = True
                    item_info = items.get_data_by_item_id(item_id)
                    item_msg = f"{item_info['level']}:{item_info['name']}"
                if big_suc:  # 大成功
                    sql_message.update_exp(user_id, give_exp * 2)
                    sql_message.do_work(user_id, 0)
                    msg = f"悬赏令结算，{msg}增加修为{give_exp * 2}"
                    # todo 战利品结算sql
                    if item_flag:
                        sql_message.send_back(user_id, item_id, item_info['name'], item_info['type'], 1)
                        msg += f"，额外获得奖励：{item_msg}!"
                    else:
                        msg += "!"
                    limit_handle.update_user_log_data(user_id, msg)
                    await bot.send(event=event, message=msg)
                    await do_work.finish()

                else:
                    sql_message.update_exp(user_id, give_exp)
                    sql_message.do_work(user_id, 0)
                    msg = f"悬赏令结算，{msg}增加修为{give_exp}"
                    if s_o_f:  # 普通成功
                        if item_flag:
                            sql_message.send_back(user_id, item_id, item_info['name'], item_info['type'], 1)
                            msg += f"，额外获得奖励：{item_msg}!"
                        else:
                            msg += "!"
                        limit_handle.update_user_log_data(user_id, msg)

                    else:  # 失败
                        msg += "!"
                        limit_handle.update_user_log_data(user_id, msg)
                    await bot.send(event=event, message=msg)
                    await do_work.finish()
        else:
            msg = "没有查到你的悬赏令信息呢，请刷新！"
            await bot.send(event=event, message=msg)
            await do_work.finish()

    elif mode == "接取":
        num = args[1]
        is_type, msg = check_user_type(user_id, 0)  # 需要无状态的用户
        if is_type:  # 接取逻辑
            if num is None or str(num) not in ['1', '2', '3']:
                msg = '请输入正确的任务序号，悬赏令接取后直接接数字，不要用空格隔开！'
                await bot.send(event=event, message=msg)
                await do_work.finish()
            work_num = 1
            try:
                if work[user_id]:
                    work_num = int(num)  # 任务序号
                try:
                    get_work = work[user_id].world[work_num - 1]
                    sql_message.do_work(user_id, 2, get_work[0])
                    del work[user_id]
                    msg = f"接取任务【{get_work[0]}】成功"

                except IndexError:
                    msg = "没有这样的任务"

            except KeyError:
                msg = "没有查到你的悬赏令信息呢，请刷新！"
        else:
            msg = "没有查到你的悬赏令信息呢，请刷新！"
        await bot.send(event=event, message=msg)
        await do_work.finish()

    elif mode == "帮助":
        msg = __work_help__
        await bot.send(event=event, message=msg)
        await do_work.finish()


@do_work.receive()
async def get_work_num(bot: Bot, event: GroupMessageEvent):
    # 这里曾经是风控模块，但是已经不再需要了
    num = get_num_from_str(event.get_plaintext())

    _, user_info, _ = check_user(event)

    user_id = user_info.get('user_id')
    is_type, msg = check_user_type(user_id, 0)  # 需要无状态的用户
    if is_type:  # 接取逻辑
        if not num:
            msg = '请输入正确的任务序号'
            await bot.send(event=event, message=msg)
            await do_work.finish()
        try:
            work_num = 1
            if work[user_id]:
                work_num = int(num[0])  # 任务序号
            try:
                get_work = work[user_id].world[work_num - 1]
                sql_message.do_work(user_id, 2, get_work[0])
                del work[user_id]
                msg = f"接取任务【{get_work[0]}】成功"
            except IndexError:
                msg = "没有这样的任务"
        except KeyError:
            msg = "没有查到你的悬赏令信息呢，请刷新！"
    await bot.send(event=event, message=msg)
    await do_work.finish()


def get_work_msg(work_):
    msg = f"{work_[0]},完成机率{work_[1]},基础报酬{work_[2]}修为,预计需{work_[3]}分钟{work_[4]}\r"
    return msg
