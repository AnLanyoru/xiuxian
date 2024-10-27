import re
import random
import asyncio
from datetime import datetime
from nonebot.typing import T_State

from ..xiuxian_buff import limit_dict
from ..xiuxian_buff.limit import CheckLimit
from ..xiuxian_limit import LimitHandle
from ..xiuxian_place import Place
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot import require, on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GROUP_ADMIN,
    GROUP_OWNER,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from nonebot.params import CommandArg
from ..xiuxian_utils.data_source import jsondata
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, XiuxianJsonDate, OtherSet,
    UserBuffDate, XIUXIAN_IMPART_BUFF, leave_harm_time
)
from ..xiuxian_config import XiuConfig, JsonConfig, convert_rank
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic, number_to,
    CommandObjectID,
    Txt2Img, send_msg_handler, get_num_from_str, get_id_from_str, get_strs_from_str
)
from ..xiuxian_utils.item_json import Items

items = Items()

# 定时任务
scheduler = require("nonebot_plugin_apscheduler").scheduler
cache_help = {}
cache_level_help = {}
sql_message = XiuxianDateManage()  # sql类
xiuxian_impart = XIUXIAN_IMPART_BUFF()

run_xiuxian = on_command("踏入仙途", aliases={"/踏入仙途", "我要修仙"}, priority=8, permission=GROUP, block=True)
restart = on_command("重入仙途", permission=GROUP, priority=7, block=True)
sign_in = on_command("修仙签到", aliases={"/签到"}, priority=13, permission=GROUP, block=True)
rank = on_command("排行榜", aliases={"修仙排行榜", "灵石排行榜", "战力排行榜", "境界排行榜", "宗门排行榜"},
                  priority=7, permission=GROUP, block=True)
rename = on_command("改头换面", aliases={"修仙改名", "改名", "改头", "换面"}, priority=5, permission=GROUP,
                    block=True)
level_up = on_command("突破", aliases={"tp"}, priority=6, permission=GROUP, block=True)
level_up_dr = on_fullmatch("渡厄突破", priority=7, permission=GROUP, block=True)
level_up_drjd = on_command("渡厄金丹突破", aliases={"金丹突破"}, priority=7, permission=GROUP, block=True)
level_up_zj = on_command("直接突破", aliases={"破", "/突破"}, priority=2, permission=GROUP, block=True)
level_up_zj_all = on_command("快速突破", aliases={"连续突破", "一键突破"}, priority=2, permission=GROUP, block=True)
give_stone = on_command("送灵石", priority=5, permission=GROUP, block=True)
steal_stone = on_command("借灵石", priority=4, permission=GROUP, block=True)
gm_command = on_command("生成灵石", permission=SUPERUSER, priority=10, block=True)
gm_command_miss = on_command("思恋结晶", permission=SUPERUSER, priority=10, block=True)
gmm_command = on_command("灵根更换", permission=SUPERUSER, priority=10, block=True)
cz = on_command('创造', permission=SUPERUSER, priority=15, block=True)
rob_stone = on_command("抢灵石", priority=5, permission=GROUP, block=True)
restate = on_command("重置用户状态", permission=SUPERUSER, priority=12, block=True)
set_xiuxian = on_command("启用修仙功能", aliases={'禁用修仙功能'},
                         permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER), priority=5, block=True)
user_leveluprate = on_command('我的突破概率', aliases={'突破概率'}, priority=5, permission=GROUP, block=True)
user_stamina = on_command('我的体力', aliases={'体力'}, priority=5, permission=GROUP, block=True)
xiuxian_update_data = on_fullmatch('更新记录', priority=15, permission=GROUP, block=True)
level_help = on_command('列表', aliases={"灵根列表", "品阶列表", "境界列表"}, priority=15, permission=GROUP, block=True)


__xiuxian_update_data__ = f"""
#更新2024.10.27
增加快速炼金系统
增加宗门周贡献系统
增加日志系统
""".strip()

__level_help_root__ = f"""\n
--灵根帮助--
轮回——异界&极道——混沌
九彩——七彩——混元
天——异——真——伪
""".strip()
__level_help_level__ = f"""\n
--境界列表--
彼岸三十三天
道无涯三境
道神九重——非语三境——圣王三境——大圣三境
圣人九重——准圣三境——仙帝三境——金仙三境
玄仙三境——地仙三境——凡仙三境——登仙三境
羽化三境——虚劫三境——合道三境——逆虚三境
炼神三境——悟道三境——天人四境——踏虚三境
通玄九重——归元九重——聚元九重——凝气九重
引气三境——感气三境——炼体九重——求道启程
""".strip()
__level_help_skill__ = f"""\n
--功法品阶--
真神&荒神
天尊——界主——神变
神极——神劫——神海——生死
虚劫——神丹——先天——后天
--法器品阶--
神器——圣器——仙器
灵器——玄器——宝器——符器
""".strip()


# 重置每日签到, 每日限额
@scheduler.scheduled_job("cron", hour=0, minute=0)
async def xiuxian_sing_():
    sql_message.sign_remake()
    logger.opt(colors=True).info(f"<green>每日修仙签到，每日限制重置成功！</green>")


@xiuxian_update_data.handle(parameterless=[Cooldown(at_sender=False)])
async def mix_elixir_help_(bot: Bot, event: GroupMessageEvent):
    """更新记录"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = __xiuxian_update_data__
    await bot.send(event=event, message=msg)
    await xiuxian_update_data.finish()




@run_xiuxian.handle(parameterless=[Cooldown(at_sender=False)])
async def run_xiuxian_(bot: Bot, event: GroupMessageEvent):
    """加入修仙"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    user_id = event.get_user_id()
    user_name = sql_message.random_name()
    #    event.sender.card if event.sender.card else event.sender.nickname
    # )  # 获取为用户名(旧)
    root, root_type = XiuxianJsonDate().linggen_get()  # 获取灵根，灵根类型
    rate = sql_message.get_root_rate(root_type)  # 灵根倍率
    power = 100 * float(rate)  # 战力=境界的power字段 * 灵根的rate字段
    create_time = str(datetime.now())
    is_new_user, msg = sql_message.create_user(
        user_id, root, root_type, int(power), create_time, user_name
    )
    try:
        if is_new_user:
            await bot.send(event=event, message=msg)
            is_user, user_msg, msg = check_user(event)
            if user_msg['hp'] is None or user_msg['hp'] == 0 or user_msg['hp'] == 0:
                sql_message.update_user_hp(user_id)
            await asyncio.sleep(1)
            msg = "耳边响起一个神秘人的声音：不要忘记仙途奇缘！!\n不知道怎么玩的话可以发送 修仙帮助 喔！！"
            await bot.send(event=event, message=msg)
        else:
            await bot.send(event=event, message=msg)
    except ActionFailed:
        await run_xiuxian.finish("修仙界网络堵塞，发送失败!", reply_message=True)


@sign_in.handle(parameterless=[Cooldown(at_sender=False)])
async def sign_in_(bot: Bot, event: GroupMessageEvent):
    """修仙签到"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await sign_in.finish()
    user_id = user_info['user_id']
    result = sql_message.get_sign(user_id)
    msg = result
    try:
        await bot.send(event=event, message=msg)
        await sign_in.finish()
    except ActionFailed:
        await sign_in.finish("修仙界网络堵塞，发送失败!", reply_message=True)


@level_help.handle(parameterless=[Cooldown(at_sender=False)])
async def level_help_(bot: Bot, event: GroupMessageEvent):
    """境界帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    message = str(event.message)
    rank_msg = r'[\u4e00-\u9fa5]+'
    message = re.findall(rank_msg, message)
    if message:
        message = message[0]
    if message in ["境界列表", "境界帮助"]:
        msg = __level_help_level__
        await bot.send(event=event, message=msg)
        await level_help.finish()
    elif message in ["灵根列表", "灵根帮助"]:
        msg = __level_help_root__
        await bot.send(event=event, message=msg)
        await level_help.finish()
    elif message in ["品阶列表", "品阶帮助"]:
        msg = __level_help_skill__
        await bot.send(event=event, message=msg)
        await level_help.finish()


@restart.handle(parameterless=[Cooldown(at_sender=False)])
async def restart_(bot: Bot, event: GroupMessageEvent, state: T_State):
    """刷新灵根信息"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await restart.finish()

    if user_info['stone'] < XiuConfig().remake:
        msg = "你的灵石还不够呢，快去赚点灵石吧！"
        await bot.send(event=event, message=msg)
        await restart.finish()

    linggen_options = []
    for _ in range(10):
        name, root_type = XiuxianJsonDate().linggen_get()
        linggen_options.append((name, root_type))

    linggen_list_msg = "\n".join(
        [f"{i + 1}. {name} ({root_type})" for i, (name, root_type) in enumerate(linggen_options)])
    choice_msg_pass = f"请从以下灵根中选择一个:\n{linggen_list_msg}\n请输入对应的数字选择 (1-10):"

    state["linggen_options"] = linggen_options
    state["linggen_msg"] = choice_msg_pass
    try:
        state["msg_pass"]
    except:
        state["msg_pass"] = 0
    if user_info["root_type"] not in ["异世界之力", "极道灵根", "轮回灵根", "源宇道根", "道之本源"] or \
            state["msg_pass"] == 3:
        await bot.send(event=event, message=choice_msg_pass)
        state["msg_pass"] = 2
    else:
        msg = f"道友的灵根为{user_info['root']}，乃是{user_info['root_type']}\n若思虑周全了欲更换灵根，请回复我【确认更换灵根】"
        await bot.send(event=event, message=msg)
        state["msg_pass"] = 1


@restart.receive()
async def handle_user_choice(bot: Bot, event: GroupMessageEvent, state: T_State):
    user_choice = event.get_plaintext().strip()
    user_id = event.get_user_id()  # 从状态中获取用户ID
    linggen_options = state["linggen_options"]
    choice_msg_pass = state["linggen_msg"]
    selected_name, selected_root_type = max(linggen_options,
                                            key=lambda x: jsondata.root_data()[x[1]]["type_speeds"])
    if state["msg_pass"] == 2:
        if user_choice.isdigit():  # 判断数字
            user_choice = get_num_from_str(user_choice)[0]
            user_choice = int(user_choice)
            if 1 <= user_choice <= 10:
                selected_name, selected_root_type = linggen_options[user_choice - 1]
                msg = f"你选择了 {selected_name} 呢！\n"
            else:
                msg = "输入有误，帮你自动选择最佳灵根了嗷！\n"
        else:
            msg = "输入有误，帮你自动选择最佳灵根了嗷！\n"

        msg += sql_message.ramaker(selected_name, selected_root_type, user_id)
        try:
            await bot.send_group_msg(group_id=event.group_id, message=msg)
        except ActionFailed:
            await bot.send_group_msg(group_id=event.group_id, message="修仙界网络堵塞，发送失败!")
            await restart.finish()
    else:
        if user_choice == "确认更换灵根":
            await bot.send_group_msg(group_id=event.group_id, message=choice_msg_pass)
            state["msg_pass"] = 2
            await restart.reject()


@rank.handle(parameterless=[Cooldown(at_sender=False)])
async def rank_(bot: Bot, event: GroupMessageEvent):
    """排行榜"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    messages = str(event.message)
    rank_msg = r'[\u4e00-\u9fa5]+'
    message = re.findall(rank_msg, messages)
    num = get_num_from_str(messages)
    if num:
        page = int(num[0])
    else:
        page = 1
    if message:
        message = message[0]
    first_msg = ""
    scened_msg = ""
    if message in ["排行榜", "修仙排行榜", "境界排行榜", "修为排行榜"]:
        lt_rank = sql_message.realm_top()
        scened_msg = "修为"
    elif message == "灵石排行榜":
        lt_rank = sql_message.stone_top()
        scened_msg = "灵石"
    elif message == "战力排行榜":
        lt_rank = sql_message.power_top()
        scened_msg = "战力"
    elif message in ["宗门排行榜", "宗门建设度排行榜"]:
        lt_rank = sql_message.scale_top()
        first_msg = "ID:"
        scened_msg = "建设度"
    else:
        lt_rank = {}
    long_rank = len(lt_rank)
    page_all = (long_rank // 20) + 1 if long_rank % 20 != 0 else long_rank // 20  # 总页数
    if page_all < page != 1:
        msg = f"{message}没有那么广阔！！！"
        await bot.send(event=event, message=msg)
        await rank.finish()
    if long_rank != 0:
        # 获取页数物品数量
        item_num = page * 20 - 20
        item_num_end = item_num + 20
        lt_rank = lt_rank[item_num:item_num_end]
        msg = f"✨诸天万界{message}TOP{item_num_end}✨\n"
        num = item_num
        for i in lt_rank:
            num += 1
            msg += f"第{num}位 {first_msg}{i[0]} {i[1]} {scened_msg}:{number_to(i[2])}\n"
        msg += f"\n第 {page}/{page_all} 页\n☆————tips————☆\n可以发送{message}+页数来查看更多{message}哦"
    else:
        msg = f"{message}空空如也！"
    await bot.send(event=event, message=msg)
    await rank.finish()


@rename.handle(parameterless=[Cooldown(at_sender=False)])
async def remaname_(bot: Bot, event: GroupMessageEvent):
    """修改道号"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await rename.finish()
    user_id = user_info['user_id']
    user_name = sql_message.random_name()
    msg = f"道友前往一处偏僻之地，施展乾坤换面诀\n霎时之间面容变换，并且修改道号为：{user_name}"
    sql_message.update_user_name(user_id, user_name)
    await bot.send(event=event, message=msg)
    await rename.finish()


@level_up.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def level_up_(bot: Bot, event: GroupMessageEvent):
    """突破"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await level_up.finish()
    user_id = user_info['user_id']
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    user_leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    level_cd = user_msg['level_up_cd']
    if level_cd:
        # 校验是否存在CD
        time_now = datetime.now()
        cd = OtherSet().date_diff(time_now, level_cd)  # 获取second
        if cd < XiuConfig().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            msg = f"目前无法突破，还需要{XiuConfig().level_up_cd - (cd // 60)}分钟"
            await bot.send(event=event, message=msg)
            await level_up.finish()
    else:
        pass

    level_name = user_msg['level']  # 用户境界
    level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    items = Items()
    pause_flag = False
    elixir_name = None
    elixir_desc = None
    if user_backs is not None:
        for back in user_backs:
            if int(back['goods_id']) == 1999:  # 检测到有对应丹药
                pause_flag = True
                elixir_name = back['goods_name']
                elixir_desc = items.get_data_by_item_id(1999)['desc']
                break
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    if pause_flag:
        msg = f"由于检测到背包有丹药：{elixir_name}，效果：{elixir_desc}，突破已经准备就绪\n请发送 ，【渡厄突破】 或 【直接突破】来选择是否使用丹药突破！\n本次突破概率为：{level_rate + user_leveluprate + number}% "
        await bot.send(event=event, message=msg)
        await level_up.finish()
    else:
        msg = f"由于检测到背包没有【渡厄丹】，突破已经准备就绪\n请发送，【直接突破】来突破！请注意，本次突破失败将会损失部分修为！\n本次突破概率为：{level_rate + user_leveluprate + number}% "
        await bot.send(event=event, message=msg)
        await level_up.finish()


@level_up_zj.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def level_up_zj_(bot: Bot, event: GroupMessageEvent):
    """直接突破"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()
    user_id = user_info['user_id']
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_cd = user_msg['level_up_cd']
    if level_cd:
        # 校验是否存在CD
        time_now = datetime.now()
        cd = OtherSet().date_diff(time_now, level_cd)  # 获取second
        if cd < XiuConfig().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            msg = f"目前无法突破，还需要{XiuConfig().level_up_cd - (cd // 60)}分钟"
            await bot.send(event=event, message=msg)
            await level_up_zj.finish()
    else:
        pass
    level_name = user_msg['level']  # 用户境界
    exp = user_msg['exp']  # 用户修为
    level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
    leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    main_exp_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
    exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    le = OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_id)
    if le == "失败":
        # 突破失败
        sql_message.updata_level_cd(user_id)  # 更新突破CD
        # 失败惩罚，随机扣减修为
        percentage = random.randint(
            XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
        )
        now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))  # 功法突破扣修为减少
        sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为

        user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
        user_buff_data = UserBuffDate(user_id)
        main_buff_data = user_buff_data.get_user_main_buff_data()
        impart_data = xiuxian_impart.get_user_info_with_id(user_id)
        impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
        main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
        hp_down = int(
            (now_exp / 2) *
            (1 + main_hp_buff + impart_hp_per) * jsondata.level_data()[user_msg['level']]["HP"]) \
            if (user_msg['hp'] - (now_exp / 2)) > 0 else 1
        nowhp = user_msg['hp'] - hp_down
        nowmp = user_msg['mp'] - now_exp if (user_msg['mp'] - now_exp) > 0 else 1
        sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
        update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
            level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
        sql_message.update_levelrate(user_id, leveluprate + update_rate)
        msg = f"道友突破失败,境界受损,修为减少{number_to(now_exp)}|{now_exp}，气血流失{hp_down}，下次突破成功率增加{update_rate}%，道友不要放弃！"
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()

    elif type(le) is list:
        # 突破成功
        sql_message.updata_level(user_id, le[0])  # 更新境界
        sql_message.update_power2(user_id)  # 更新战力
        sql_message.updata_level_cd(user_id)  # 更新CD
        sql_message.update_levelrate(user_id, 0)
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"恭喜道友突破{le[0]}成功！"
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()
    else:
        # 最高境界
        msg = le
        await bot.send(event=event, message=msg)
        await level_up_zj.finish()


@level_up_zj_all.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def level_up_zj_all_(bot: Bot, event: GroupMessageEvent):
    """快速突破"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await level_up_zj_all.finish()
    run = 0
    user_id = user_info['user_id']
    lost_exp = 0
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_name = user_msg['level']  # 用户境界
    exp = user_msg['exp']  # 用户修为
    level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
    leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    msg = "开始进行快速突破\n———————————————\n"
    while "道友" not in OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_id):
        run = 1
        if user_info['hp'] is None:
            # 判断用户气血是否为空
            sql_message.update_user_hp(user_id)
        user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
        level_name = user_msg['level']  # 用户境界
        exp = user_msg['exp']  # 用户修为
        level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
        leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
        main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升，别忘了还有渡厄突破
        main_exp_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
        exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
        number = main_rate_buff['number'] if main_rate_buff is not None else 0
        le = OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_id)
        if le == "失败":
            # 突破失败
            sql_message.updata_level_cd(user_id)  # 更新突破CD
            # 失败惩罚，随机扣减修为
            percentage = random.randint(
                XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
            )
            now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))  # 功法突破扣修为减少
            sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为

            user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
            user_buff_data = UserBuffDate(user_id)
            main_buff_data = user_buff_data.get_user_main_buff_data()
            impart_data = xiuxian_impart.get_user_info_with_id(user_id)
            impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
            main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
            hp_down = int(
                (now_exp / 2) * (1 + main_hp_buff + impart_hp_per) * jsondata.level_data()[user_msg['level']]["HP"]) \
                if (user_msg['hp'] - (now_exp / 2)) > 0 else 1
            nowhp = user_msg['hp'] - hp_down
            nowmp = user_msg['mp'] - now_exp if (user_msg['mp'] - now_exp) > 0 else 1
            sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            sql_message.update_levelrate(user_id, leveluprate + update_rate)
            msg += f"道友突破失败,境界受损,修为减少{number_to(now_exp)}|{now_exp}，气血流失{hp_down}，下次突破成功率增加{update_rate}%，道友不要放弃！\n"
            lost_exp += now_exp
        elif type(le) is list:
            # 突破成功
            sql_message.updata_level(user_id, le[0])  # 更新境界
            sql_message.update_power2(user_id)  # 更新战力
            sql_message.updata_level_cd(user_id)  # 更新CD
            sql_message.update_levelrate(user_id, 0)
            sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
            msg += f"恭喜道友突破{le[0]}成功！\n"

        else:
            # 最高境界
            msg += le + "\n"
    final_level = sql_message.get_user_info_with_id(user_id)["level"]
    if run == 1:
        msg += f"———————————————\n快速突破结束本次快速突破损失{number_to(lost_exp)}|{lost_exp}点修为\n成功突破至{final_level}"
    else:
        msg += OtherSet().get_type(exp, level_rate + leveluprate + number, level_name, user_id)
    await bot.send(event=event, message=msg)
    await level_up_zj_all.finish()


@level_up_drjd.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def level_up_drjd_(bot: Bot, event: GroupMessageEvent):
    """渡厄 金丹 突破"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await level_up_drjd.finish()
    user_id = user_info['user_id']
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_cd = user_msg['level_up_cd']
    if level_cd:
        # 校验是否存在CD
        time_now = datetime.now()
        cd = OtherSet().date_diff(time_now, level_cd)  # 获取second
        if cd < XiuConfig().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            msg = f"目前无法突破，还需要{XiuConfig().level_up_cd - (cd // 60)}分钟"
            await bot.send(event=event, message=msg)
            await level_up_drjd.finish()
    else:
        pass
    elixir_name = "渡厄金丹"
    level_name = user_msg['level']  # 用户境界
    exp = user_msg['exp']  # 用户修为
    level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
    user_leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    le = OtherSet().get_type(exp, level_rate + user_leveluprate + number, level_name, user_id)
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    pause_flag = False
    if user_backs is not None:
        for back in user_backs:
            if int(back['goods_id']) == 1998:  # 检测到有对应丹药
                pause_flag = True
                elixir_name = back['goods_name']
                break

    if not pause_flag:
        msg = f"道友突破需要使用{elixir_name}，但您的背包中没有该丹药！"
        await bot.send(event=event, message=msg)
        await level_up_drjd.finish()

    if le == "失败":
        # 突破失败
        sql_message.updata_level_cd(user_id)  # 更新突破CD
        if pause_flag:
            # 使用丹药减少的sql
            sql_message.update_back_j(user_id, 1998, use_key=1)
            now_exp = int(int(exp) * 0.1)
            sql_message.update_exp(user_id, now_exp)  # 渡厄金丹增加用户修为
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            sql_message.update_levelrate(user_id, user_leveluprate + update_rate)
            msg = f"道友突破失败，但是使用了丹药{elixir_name}，本次突破失败不扣除修为反而增加了一成，下次突破成功率增加{update_rate}%！！"
        else:
            # 失败惩罚，随机扣减修为
            percentage = random.randint(
                XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
            )
            main_exp_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
            exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
            now_exp = int(int(exp) * ((percentage / 100) * exp_buff))
            sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为
            user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
            user_buff_data = UserBuffDate(user_id)
            main_buff_data = user_buff_data.get_user_main_buff_data()
            impart_data = xiuxian_impart.get_user_info_with_id(user_id)
            impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
            main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0

            nowhp = user_msg['hp'] - int(
                (now_exp / 2) * (1 + main_hp_buff + impart_hp_per) * jsondata.level_data()[user_msg['level']][
                    "HP"]) if (user_msg['hp'] - (now_exp / 2)) > 0 else 1
            nowmp = user_msg['mp'] - now_exp if (user_msg['mp'] - now_exp) > 0 else 1
            sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            sql_message.update_levelrate(user_id, user_leveluprate + update_rate)
            msg = f"没有检测到{elixir_name}，道友突破失败,境界受损,修为减少{now_exp}，下次突破成功率增加{update_rate}%，道友不要放弃！"
        await bot.send(event=event, message=msg)
        await level_up_drjd.finish()

    elif type(le) is list:
        # 突破成功
        sql_message.updata_level(user_id, le[0])  # 更新境界
        sql_message.update_power2(user_id)  # 更新战力
        sql_message.updata_level_cd(user_id)  # 更新CD
        sql_message.update_levelrate(user_id, 0)
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        now_exp = int(int(exp) * 0.1)
        sql_message.update_exp(user_id, now_exp)  # 渡厄金丹增加用户修为
        msg = f"恭喜道友突破{le[0]}成功，因为使用了渡厄金丹，修为也增加了一成！！"
        await bot.send(event=event, message=msg)
        await level_up_drjd.finish()
    else:
        # 最高境界
        msg = le
        await bot.send(event=event, message=msg)
        await level_up_drjd.finish()


@level_up_dr.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def level_up_dr_(bot: Bot, event: GroupMessageEvent):
    """渡厄 突破"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()
    user_id = user_info['user_id']
    if user_info['hp'] is None:
        # 判断用户气血是否为空
        sql_message.update_user_hp(user_id)
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    level_cd = user_msg['level_up_cd']
    if level_cd:
        # 校验是否存在CD
        time_now = datetime.now()
        cd = OtherSet().date_diff(time_now, level_cd)  # 获取second
        if cd < XiuConfig().level_up_cd * 60:
            # 如果cd小于配置的cd，返回等待时间
            msg = f"目前无法突破，还需要{XiuConfig().level_up_cd - (cd // 60)}分钟"
            await bot.send(event=event, message=msg)
            await level_up_dr.finish()
    else:
        pass
    elixir_name = "渡厄丹"
    level_name = user_msg['level']  # 用户境界
    exp = user_msg['exp']  # 用户修为
    level_rate = jsondata.level_rate_data()[level_name]  # 对应境界突破的概率
    user_leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    le = OtherSet().get_type(exp, level_rate + user_leveluprate + number, level_name, user_id)
    user_backs = sql_message.get_back_msg(user_id)  # list(back)
    pause_flag = False
    if user_backs is not None:
        for back in user_backs:
            if int(back['goods_id']) == 1999:  # 检测到有对应丹药
                pause_flag = True
                elixir_name = back['goods_name']
                break

    if not pause_flag:
        msg = f"道友突破需要使用{elixir_name}，但您的背包中没有该丹药！"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()

    if le == "失败":
        # 突破失败
        sql_message.updata_level_cd(user_id)  # 更新突破CD
        if pause_flag:
            # todu，丹药减少的sql
            sql_message.update_back_j(user_id, 1999, use_key=1)
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            sql_message.update_levelrate(user_id, user_leveluprate + update_rate)
            msg = f"道友突破失败，但是使用了丹药{elixir_name}，本次突破失败不扣除修为下次突破成功率增加{update_rate}%，道友不要放弃！"
        else:
            # 失败惩罚，随机扣减修为
            percentage = random.randint(
                XiuConfig().level_punishment_floor, XiuConfig().level_punishment_limit
            )
            main_exp_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破扣修为减少
            exp_buff = main_exp_buff['exp_buff'] if main_exp_buff is not None else 0
            now_exp = int(int(exp) * ((percentage / 100) * (1 - exp_buff)))
            sql_message.update_j_exp(user_id, now_exp)  # 更新用户修为
            user_msg = XiuxianDateManage().get_user_info_with_id(user_id)
            user_buff_data = UserBuffDate(user_id)
            main_buff_data = user_buff_data.get_user_main_buff_data()
            impart_data = xiuxian_impart.get_user_info_with_id(user_id)
            impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
            main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0

            nowhp = user_msg['hp'] - int(
                (now_exp / 2) * (1 + main_hp_buff + impart_hp_per) * jsondata.level_data()[user_msg['level']][
                    "HP"]) if (user_msg['hp'] - (now_exp / 2)) > 0 else 1
            nowmp = user_msg['mp'] - now_exp if (user_msg['mp'] - now_exp) > 0 else 1
            sql_message.update_user_hp_mp(user_id, nowhp, nowmp)  # 修为掉了，血量、真元也要掉
            update_rate = 1 if int(level_rate * XiuConfig().level_up_probability) <= 1 else int(
                level_rate * XiuConfig().level_up_probability)  # 失败增加突破几率
            sql_message.update_levelrate(user_id, user_leveluprate + update_rate)
            msg = f"没有检测到{elixir_name}，道友突破失败,境界受损,修为减少{now_exp}，下次突破成功率增加{update_rate}%，道友不要放弃！"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()

    elif type(le) is list:
        # 突破成功
        sql_message.updata_level(user_id, le[0])  # 更新境界
        sql_message.update_power2(user_id)  # 更新战力
        sql_message.updata_level_cd(user_id)  # 更新CD
        sql_message.update_levelrate(user_id, 0)
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"恭喜道友突破{le[0]}成功"
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()
    else:
        # 最高境界
        msg = le
        await bot.send(event=event, message=msg)
        await level_up_dr.finish()


@user_leveluprate.handle(parameterless=[Cooldown(at_sender=False)])
async def user_leveluprate_(bot: Bot, event: GroupMessageEvent):
    """我的突破概率"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await user_leveluprate.finish()
    user_id = user_info['user_id']
    user_msg = sql_message.get_user_info_with_id(user_id)  # 用户信息
    leveluprate = int(user_msg['level_up_rate'])  # 用户失败次数加成
    level_name = user_msg['level']  # 用户境界
    level_rate = jsondata.level_rate_data()[level_name]  # 
    main_rate_buff = UserBuffDate(user_id).get_user_main_buff_data()  # 功法突破概率提升
    number = main_rate_buff['number'] if main_rate_buff is not None else 0
    msg = f"道友下一次突破成功概率为{level_rate + leveluprate + number}%"
    await bot.send(event=event, message=msg)
    await user_leveluprate.finish()


@user_stamina.handle(parameterless=[Cooldown(at_sender=False)])
async def user_stamina_(bot: Bot, event: GroupMessageEvent):
    """我的体力信息"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        await bot.send(event=event, message=msg)
        await user_stamina.finish()
    msg = f"当前体力：{user_info['user_stamina']}"
    await bot.send(event=event, message=msg)
    await user_stamina.finish()


@give_stone.handle(parameterless=[Cooldown(at_sender=False)])
async def give_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """送灵石"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await give_stone.finish()
    user_id = user_info['user_id']
    user_name = user_info['user_name']
    user_stone_num = user_info['stone']
    msg = args.extract_plain_text()
    stone_num = get_num_from_str(msg)
    give_qq = get_id_from_str(msg)  # 使用道号获取用户id，代替原at
    if stone_num:
        give_stone_num = stone_num[0]
    else:
        stone_num = None
        give_stone_num = 0
    if stone_num:
        if int(give_stone_num) > int(user_stone_num):
            msg = f"道友的灵石不够，请重新输入！"
            await bot.send(event=event, message=msg)
            await give_stone.finish()
    else:
        msg = f"请输入正确的灵石数量！！！"
        await bot.send(event=event, message=msg)
        await give_stone.finish()
    if give_qq:
        if str(give_qq) == str(user_id):
            msg = f"请不要送灵石给自己！"
            await bot.send(event=event, message=msg)
            await give_stone.finish()
        else:
            give_user = sql_message.get_user_info_with_id(give_qq)
            if give_user:
                if Place().is_the_same_world(give_qq, user_id) is False:
                    msg = f"\n{give_user['user_name']}道友与你不在同一位面，无法赠送！！！跨位面赠送灵石费用及其昂贵！！！"
                    await bot.send(event=event, message=msg)
                    await give_stone.finish()
                if Place().is_the_same_place(give_qq, user_id):
                    num = int(give_stone_num)
                    sql_message.update_ls(user_id, give_stone_num, 2)  # 减少用户灵石
                    sql_message.update_ls(give_qq, num, 1)  # 增加用户灵石
                    msg = give_user['user_name'] + "道友" + str(num) + "灵石"
                    msg = f"\n{user_name}道友与好友在同一位置，当面赠送：\n" + msg
                    LimitHandle().update_user_log_data(user_id, msg)
                    LimitHandle().update_user_log_data(give_qq, msg)
                    await bot.send(event=event, message=msg)
                    await give_stone.finish()

                give_stone_num2 = int(give_stone_num) * 0.1
                num = int(give_stone_num) - int(give_stone_num2)
                sql_message.update_ls(user_id, give_stone_num, 2)  # 减少用户灵石
                sql_message.update_ls(give_qq, num, 1)  # 增加用户灵石
                msg = give_user['user_name'] + "道友" + str(num) + "灵石"
                msg = (f"\n{user_name}道友与好友不在一地，通过远程邮寄赠送：\n" + msg +
                       f"\n收取远程邮寄手续费{(number_to(give_stone_num2))}|{int(give_stone_num2)}枚！")
                LimitHandle().update_user_log_data(user_id, msg)
                LimitHandle().update_user_log_data(give_qq, msg)
                await bot.send(event=event, message=msg)
                await give_stone.finish()
            else:
                msg = f"对方未踏入修仙界，不可赠送！"
                await bot.send(event=event, message=msg)
                await give_stone.finish()
    else:
        msg = f"未获到对方信息，请输入正确的道号！"
        await bot.send(event=event, message=msg)
        await give_stone.finish()


# 偷灵石
@steal_stone.handle(parameterless=[Cooldown(stamina_cost=2400, at_sender=False)])
async def steal_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    args = args.extract_plain_text().split()
    if not isUser:
        await bot.send(event=event, message=msg)
        await steal_stone.finish()
    user_id = user_info['user_id']
    steal_user = None
    steal_user_stone = None
    user_stone_num = user_info['stone']
    coststone_num = XiuConfig().tou
    if int(coststone_num) > int(user_stone_num):
        msg = f"道友的偷窃准备(灵石)不足，请打工之后再切格瓦拉！"
        sql_message.update_user_stamina(user_id, 1000, 1)
        await bot.send(event=event, message=msg)
        await steal_stone.finish()
    steal_qq = sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at
    if steal_qq:
        if steal_qq == user_id:
            msg = f"请不要偷自己刷成就！"
            sql_message.update_user_stamina(user_id, 1000, 1)
            await bot.send(event=event, message=msg)
            await steal_stone.finish()
        else:
            steal_user = sql_message.get_user_info_with_id(steal_qq)
            if steal_user:
                steal_user_stone = steal_user['stone']
    if steal_user:
        steal_success = random.randint(0, 100)
        result = OtherSet().get_power_rate(user_info['power'], steal_user['power'])
        if isinstance(result, int):
            if int(steal_success) > result:
                sql_message.update_ls(user_id, coststone_num, 2)  # 减少手续费
                sql_message.update_ls(steal_qq, coststone_num, 1)  # 增加被偷的人的灵石
                msg = f"道友偷窃失手了，被对方发现并被派去义务劳工！赔款{coststone_num}灵石"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
            get_stone = random.randint(int(XiuConfig().tou_lower_limit * steal_user_stone),
                                       int(XiuConfig().tou_upper_limit * steal_user_stone))
            if int(get_stone) > int(steal_user_stone):
                sql_message.update_ls(user_id, steal_user_stone, 1)  # 增加偷到的灵石
                sql_message.update_ls(steal_qq, steal_user_stone, 2)  # 减少被偷的人的灵石
                msg = f"{steal_user['user_name']}道友已经被榨干了~"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
            else:
                sql_message.update_ls(user_id, get_stone, 1)  # 增加偷到的灵石
                sql_message.update_ls(steal_qq, get_stone, 2)  # 减少被偷的人的灵石
                msg = f"共偷取{steal_user['user_name']}道友{number_to(get_stone)}枚灵石！"
                await bot.send(event=event, message=msg)
                await steal_stone.finish()
        else:
            msg = result
            await bot.send(event=event, message=msg)
            await steal_stone.finish()
    else:
        msg = f"对方未踏入修仙界，不要对凡人出手！"
        await bot.send(event=event, message=msg)
        await steal_stone.finish()


# GM加灵石
@gm_command.handle(parameterless=[Cooldown(at_sender=False)])
async def gm_command_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg_text = args.extract_plain_text()
    stone_num_match = re.findall(r"\d+", msg_text)  # 提取数字
    give_qq = get_id_from_str(msg_text)  # 道号
    command_target = get_strs_from_str(msg_text)
    if command_target:
        command_target = command_target[0]
    else:
        command_target = None
    give_stone_num = int(stone_num_match[0]) if stone_num_match else 0  # 默认灵石数为0，如果有提取到数字，则使用提取到的第一个数字
    if give_qq:
        give_user = sql_message.get_user_info_with_id(give_qq)
        sql_message.update_ls(give_qq, give_stone_num, 1)  # 增加用户灵石
        msg = f"共赠送{number_to(give_stone_num)}枚灵石给{give_user['user_name']}道友！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    elif command_target == "all":
        sql_message.update_ls_all(give_stone_num)
        msg = f"赠送所有用户{give_stone_num}灵石,请注意查收！"
        await bot.send(event=event, message=msg)
    else:
        msg = f"对方未踏入修仙界，不可赠送！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    await gm_command.finish()


# GM加思恋结晶
@gm_command_miss.handle(parameterless=[Cooldown(at_sender=False)])
async def gm_command_miss_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg_text = args.extract_plain_text()
    stone_num_match = re.findall(r"\d+", msg_text)  # 提取数字
    give_qq = get_id_from_str(msg_text)  # 道号
    command_target = get_strs_from_str(msg_text)
    if command_target:
        command_target = command_target[0]
    else:
        command_target = None
    give_stone_num = int(stone_num_match[0]) if stone_num_match else 0  # 默认灵石数为0，如果有提取到数字，则使用提取到的第一个数字
    if give_qq:
        give_user = sql_message.get_user_info_with_id(give_qq)
        await xiuxian_impart.update_stone_num(give_stone_num, give_qq, 1)
        msg = f"共赠送{number_to(give_stone_num)}颗思恋结晶给{give_user['user_name']}道友！"
        await bot.send(event=event, message=msg)
        await gm_command_miss.finish()
    elif command_target == "all":
        xiuxian_impart.update_impart_stone_all(give_stone_num)
        msg = f"赠送所有用户{give_stone_num}思恋结晶,请注意查收！"
        await bot.send(event=event, message=msg)
    else:
        msg = f"对方未踏入修仙界，不可赠送！"
        await bot.send(event=event, message=msg)
        await gm_command.finish()
    await gm_command_miss.finish()


@cz.handle(parameterless=[Cooldown(at_sender=False)])
async def cz_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """创造物品"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = args.extract_plain_text()
    strs = get_strs_from_str(msg)
    nums = get_num_from_str(msg)
    if strs:
        goods_name = strs[0]
        if len(strs) > 1:
            send_name = strs[1]
        else:
            send_name = None
    else:
        goods_name = None
        send_name = None
        msg = f"请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
        await bot.send(event=event, message=msg)
        await cz.finish()
    if nums:
        goods_num = int(nums[0])
    else:
        goods_num = 1
    goods_id = -1
    goods_type = None
    is_item = False
    for k, v in items.items.items():
        if goods_name == v['name']:
            goods_id = k
            goods_type = v['type']
            is_item = True
            break
        else:
            continue
    if is_item:
        pass
    else:
        msg = f"物品不存在！！！"
        await bot.send(event=event, message=msg)
        await cz.finish()
    give_qq = sql_message.get_user_id(send_name)  # 使用道号获取用户id，代替原at
    if give_qq:
        give_user = sql_message.get_user_info_with_id(give_qq)
        if give_user:
            sql_message.send_back(give_qq, goods_id, goods_name, goods_type, goods_num, 1)
            msg = f"{give_user['user_name']}道友获得了系统赠送的{goods_num}个{goods_name}！"
        else:
            msg = f"对方未踏入修仙界，不可赠送！"
    elif send_name == "all":
        all_users = sql_message.get_all_user_id()
        for user_id in all_users:
            sql_message.send_back(user_id, goods_id, goods_name, goods_type, goods_num, 1)  # 给每个用户发送物品
        msg = f"赠送所有用户{goods_name}{goods_num}个,请注意查收！"
    else:
        msg = "请输入正确指令！例如：创造 物品 道号 数量 (道号为all赠送所有用户)"
    await bot.send(event=event, message=msg)
    await cz.finish()


# GM改灵根
@gmm_command.handle(parameterless=[Cooldown(at_sender=False)])
async def gmm_command_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = args.extract_plain_text().strip()
    if not args:
        msg = f"请输入正确指令！例如：灵根更换 x(1为混沌,2为融合,3为超,4为龙,5为天,6为千世,7为万世,8为无上)"
        await bot.send(event=event, message=msg)
        await gm_command.finish()

    give_qq = sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at

    give_user = sql_message.get_user_info_with_id(give_qq)
    if give_user:
        root_name = sql_message.update_root(give_qq, msg)
        sql_message.update_power2(give_qq)
        msg = f"{give_user['user_name']}道友的灵根已变更为{root_name}！"
        await bot.send(event=event, message=msg)
        await gmm_command.finish()
    else:
        msg = f"对方未踏入修仙界，不可修改！"
        await bot.send(event=event, message=msg)
        await gmm_command.finish()


@rob_stone.handle(parameterless=[Cooldown(stamina_cost=0, at_sender=False)])
async def rob_stone_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """抢劫
            player1 = {
            "NAME": player,
            "HP": player,
            "ATK": ATK,
            "COMBO": COMBO
        }"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await give_stone.finish()
    user_id = user_info["user_id"]
    user_mes = sql_message.get_user_info_with_id(user_id)
    give_qq = sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at
    player1 = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '爆伤': None,
               '防御': 0}
    player2 = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '爆伤': None,
               '防御': 0}
    user_2 = sql_message.get_user_info_with_id(give_qq)
    if user_mes and user_2:
        if user_info['root'] == "器师":
            msg = f"目前职业无法抢劫！"
            sql_message.update_user_stamina(user_id, 1500, 1)
            await bot.send(event=event, message=msg)
            await rob_stone.finish()

        if give_qq:
            if str(give_qq) == str(user_id):
                msg = f"请不要抢自己刷成就！"
                sql_message.update_user_stamina(user_id, 1500, 1)
                await bot.send(event=event, message=msg)
                await rob_stone.finish()

            if user_2['root'] == "器师":
                msg = f"对方职业无法被抢劫！"
                sql_message.update_user_stamina(user_id, 1500, 1)
                await bot.send(event=event, message=msg)
                await rob_stone.finish()

            if user_2:
                if user_info['hp'] is None:
                    # 判断用户气血是否为None
                    sql_message.update_user_hp(user_id)
                    user_info = sql_message.get_user_info_with_id(user_id)
                if user_2['hp'] is None:
                    sql_message.update_user_hp(give_qq)
                    user_2 = sql_message.get_user_info_with_id(give_qq)

                if user_2['hp'] <= user_2['exp'] / 10:
                    time_2 = leave_harm_time(give_qq)
                    msg = f"对方重伤藏匿了，无法抢劫！距离对方脱离生命危险还需要{time_2}分钟！"
                    sql_message.update_user_stamina(user_id, 1500, 1)
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

                if user_info['hp'] <= user_info['exp'] / 10:
                    time_msg = leave_harm_time(user_id)
                    msg = f"重伤未愈，动弹不得！距离脱离生命危险还需要{time_msg}分钟！"
                    msg += f"请道友进行闭关，或者使用药品恢复气血，不要干等，没有自动回血！！！"
                    sql_message.update_user_stamina(user_id, 1500, 1)
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

                impart_data_1 = xiuxian_impart.get_user_info_with_id(user_id)
                player1['user_id'] = user_info['user_id']
                player1['道号'] = user_info['user_name']
                player1['气血'] = 1
                player1['攻击'] = 1
                player1['真元'] = user_info['mp']
                player1['会心'] = int(
                    (0.01 + impart_data_1['impart_know_per'] if impart_data_1 is not None else 0) * 100)
                player1['爆伤'] = int(
                    1.5 + impart_data_1['impart_burst_per'] if impart_data_1 is not None else 0)
                user_buff_data = UserBuffDate(user_id)
                user_armor_data = user_buff_data.get_user_armor_buff_data()
                if user_armor_data is not None:
                    def_buff = int(user_armor_data['def_buff'])
                else:
                    def_buff = 0
                player1['防御'] = def_buff

                impart_data_2 = xiuxian_impart.get_user_info_with_id(user_2['user_id'])
                player2['user_id'] = user_2['user_id']
                player2['道号'] = user_2['user_name']
                player2['气血'] = user_2['hp']
                player2['攻击'] = user_2['atk']
                player2['真元'] = user_2['mp']
                player2['会心'] = int(
                    (0.01 + impart_data_2['impart_know_per'] if impart_data_2 is not None else 0) * 100)
                player2['爆伤'] = int(
                    1.5 + impart_data_2['impart_burst_per'] if impart_data_2 is not None else 0)
                user_buff_data = UserBuffDate(user_2['user_id'])
                user_armor_data = user_buff_data.get_user_armor_buff_data()
                if user_armor_data is not None:
                    def_buff = int(user_armor_data['def_buff'])
                else:
                    def_buff = 0
                player2['防御'] = def_buff

                result, victor = OtherSet().player_fight(player1, player2)
                await send_msg_handler(bot, event, '决斗场', bot.self_id, result)
                if victor == player1['道号']:
                    foe_stone = user_2['stone']
                    if foe_stone > 0:
                        exps = int(user_2['exp'] * 0.005)
                        msg = f"大战一番，战胜对手，获取灵石{number_to(foe_stone * 0.1)}枚，修为增加{number_to(exps)}，对手修为减少{number_to(exps / 2)}， 你不应该看见这个，重写版战斗系统灰度中！！"
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()
                    else:
                        exps = int(user_2['exp'] * 0.005)
                        msg = (f"大战一番，战胜对手，结果对方是个穷光蛋，修为增加{number_to(exps)}，对手修为减少{number_to(exps / 2)}........"
                               f"实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()

                elif victor == player2['道号']:
                    mind_stone = user_info['stone']
                    if mind_stone > 0:
                        exps = int(user_info['exp'] * 0.005)
                        msg = (f"大战一番，被对手反杀，损失灵石{number_to(mind_stone * 0.1)}枚，修为减少{number_to(exps)}，对手获取灵石{number_to(mind_stone * 0.1)}枚，修为增加{number_to(exps / 2)}"
                               f"。。。。。。实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()
                    else:
                        exps = int(user_info['exp'] * 0.005)
                        msg = (f"大战一番，被对手反杀，修为减少{number_to(exps)}，对手修为增加{number_to(exps / 2)}，，，，，，，，"
                               f"实际上没有，重写版战斗系统灰度中！！")
                        if XiuConfig().img:
                            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                            await bot.send(event=event, message=MessageSegment.image(pic))
                        else:
                            await bot.send(event=event, message=msg)
                        await rob_stone.finish()

                else:
                    msg = f"发生错误，请检查后台！"
                    await bot.send(event=event, message=msg)
                    await rob_stone.finish()

    else:
        msg = f"对方未踏入修仙界，不可抢劫！"
        await bot.send(event=event, message=msg)
        await rob_stone.finish()


@restate.handle(parameterless=[Cooldown(at_sender=False)])
async def restate_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """重置用户状态。
    单用户：重置状态@xxx
    多用户：重置状态"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    is_user, user_info, msg = check_user(event)
    if not is_user:
        await bot.send(event=event, message=msg)
        await restate.finish()
    give_qq = sql_message.get_user_id(args)  # 使用道号获取用户id，代替原at
    if give_qq:
        sql_message.restate(give_qq)
        msg = f"{give_qq}用户信息重置成功！"
        await bot.send(event=event, message=msg)
        await restate.finish()
    else:
        sql_message.restate()
        msg = f"所有用户信息重置成功！"
        await bot.send(event=event, message=msg)
        await restate.finish()


@set_xiuxian.handle()
async def open_xiuxian_(bot: Bot, event: GroupMessageEvent):
    """群修仙开关配置"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    group_msg = str(event.message)
    group_id = str(event.group_id)
    conf_data = JsonConfig().read_data()

    if "启用" in group_msg:
        if group_id not in conf_data["group"]:
            msg = "当前群聊修仙模组已启用，请勿重复操作！"
            await bot.send(event=event, message=msg)
            await set_xiuxian.finish()
        JsonConfig().write_data(2, group_id)
        msg = "当前群聊修仙基础模组已启用，快发送 踏入仙途 加入修仙世界吧！"
        await bot.send(event=event, message=msg)
        await set_xiuxian.finish()

    elif "禁用" in group_msg:
        if group_id in conf_data["group"]:
            msg = "当前群聊修仙模组已禁用，请勿重复操作！"
            await bot.send(event=event, message=msg)
            await set_xiuxian.finish()
        JsonConfig().write_data(1, group_id)
        msg = "当前群聊修仙基础模组已禁用！"
        await bot.send(event=event, message=msg)
        await set_xiuxian.finish()
    else:
        msg = "指令错误，请输入：启用修仙功能/禁用修仙功能"
        await bot.send(event=event, message=msg)
        await set_xiuxian.finish()
