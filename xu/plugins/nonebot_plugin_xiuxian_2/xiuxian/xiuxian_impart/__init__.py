import operator
import os
from base64 import b64encode
from io import BytesIO
from pathlib import Path
import random
from nonebot import on_command, on_fullmatch
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic, send_msg_handler,
    CommandObjectID
)
from ..xiuxian_utils.clean_utils import get_num_from_str, main_md
from .impart_uitls import impart_check, get_rank, re_impart_data, get_rank_plus
from .impart_data import impart_data_json
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XIUXIAN_IMPART_BUFF
from .. import NICKNAME

xiuxian_impart = XIUXIAN_IMPART_BUFF()

cache_help = {}
img_path = Path(f"{os.getcwd()}/data/xiuxian/卡图")

def img2b64(out_img) -> str:
    """ 将图片转换为base64 """
    buf = BytesIO()
    out_img.save(buf, format="PNG")
    base64_str = "base64://" + b64encode(buf.getvalue()).decode()
    return base64_str


impart_draw_fast = on_command("连续抽卡", aliases={"传承抽卡"}, priority=16, permission=GROUP, block=True)
impart_back = on_command("传承背包", aliases={"我的传承背包"}, priority=15, permission=GROUP, block=True)
impart_info = on_command("传承信息", aliases={"我的传承信息", "我的传承"}, priority=10, permission=GROUP, block=True)
impart_help = on_command("传承帮助", aliases={"虚神界帮助"}, priority=8, permission=GROUP, block=True)
re_impart_load = on_fullmatch("加载传承数据", priority=45, permission=GROUP, block=True)
impart_img = on_command("传承卡图", aliases={"传承卡片"}, priority=50, permission=GROUP, block=True)
__impart_help__ = f"""
传承帮助信息:
指令:
1、传承抽卡:
> 使用思恋结晶获取一次传承卡片(抽到的卡片被动加成)
2、传承信息:
> 获取传承主要信息
3、传承背包:
> 获取传承全部信息
4、加载传承数据:
> 重新从卡片中加载所有传承属性(数据显示有误时可用)
5、传承卡图:
> 加上卡片名字获取传承卡牌详情
6、虚神界对决:
> 进入虚神界与{NICKNAME}进行对决
7、虚神界闭关:
> 进入虚神界内闭关修炼，效率是外界闭关的6倍
—————tips——————
思恋结晶获取方式:虚神界对决
每日有一次与{NICKNAME}进行虚神界对决
{NICKNAME}会根据你的表现给予思恋结晶
如果你有很多思恋结晶可以使用连续抽卡+次数进行多次抽卡哦
"""


@impart_help.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """传承帮助"""
    # 这里曾经是风控模块，但是已经不再需要了
    msg = __impart_help__
    await bot.send(event=event, message=msg)
    await impart_help.finish()


@impart_img.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_img_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """传承卡图"""
    # 这里曾经是风控模块，但是已经不再需要了
    img_name = args.extract_plain_text().strip()
    all_data = impart_data_json.data_all_()
    x = img_name
    try:
        test = all_data[x]["type"]
        pass
    except KeyError:
        msg = f"没有找到此卡图！"
        await bot.send(event=event, message=msg)
        await impart_img.finish()
    msg = f"\r传承卡图：{img_name}\r效果：\r"
    if all_data[x]["type"] == "impart_two_exp":
        msg += "每日双修次数提升：" + str(all_data[x]["vale"])
    elif all_data[x]["type"] == "impart_exp_up":
        msg += "闭关经验提升：" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_atk_per":
        msg += "攻击力提升：" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_hp_per":
        msg += "气血提升：" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_mp_per":
        msg += "真元提升" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "boss_atk":
        msg += "boss战攻击提升" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_know_per":
        msg += "会心提升：" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_burst_per":
        msg += "会心伤害提升：" + str(all_data[x]["vale"]*100) + "%"
    elif all_data[x]["type"] == "impart_mix_per":
        msg += "炼丹收取数量增加：" + str(all_data[x]["vale"])
    elif all_data[x]["type"] == "impart_reap_per":
        msg += "灵田收取数量增加：" + str(all_data[x]["vale"])
    else:
        pass
    await bot.send(event=event, message=msg)
    await impart_img.finish()


@impart_draw_fast.handle(parameterless=[Cooldown(cd_time=5, at_sender=False)])
async def impart_draw_fast_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """传承抽卡多次"""

    _, user_info, _ = check_user(event)
    user_id = user_info['user_id']
    arg = args.extract_plain_text()
    num = get_num_from_str(arg)
    num = int(num[0]) if num else 1
    impart_data_draw = await impart_check(user_id)
    fail_msg = [f"道友思恋结晶不足{num}个！！无法进行{num}次抽卡!"] if impart_data_draw.get('stone_num', 0) < num else []
    fail_msg += f"{num}次抽卡也太多拉！！100次100次慢慢来吧！！" if 100 < num else []
    if fail_msg:
        await bot.send(event=event, message='\r'.join(fail_msg))
        await impart_draw_fast.finish()
    card = 0
    img_list = impart_data_json.data_all_keys()
    user_impart_data = xiuxian_impart.get_user_info_with_id(user_id)
    wish_count = user_impart_data.get('wish')
    msg = f"道友{user_info['user_name']}的传承抽卡"
    await xiuxian_impart.update_stone_num(num, user_id, 2)
    for i in range(num):
        # 抽 num * 10 次
        if get_rank_plus(wish_count):
            card += 1
            wish_count = 0
        else:
            wish_count += 10
    card_dict = {'had': [], 'new': []}
    for _ in range(card):
        reap_img = random.choice(img_list)
        card_status = 'had' if impart_data_json.data_person_add(user_id, reap_img) else 'new'
        card_dict[card_status].append(reap_img)
    text = ''
    if had_card := card_dict['had']:
        text += f"获取重复传承卡片{'、'.join(had_card)}\r"
        text += f"已转化为{len(had_card)*45}分钟余剩虚神界内闭关时间\r"
    if new_card := card_dict['new']:
        text += f"获取新传承卡片{'、'.join(new_card)}\r"
    all_time = (num * 50) - (card * 5) + (len(had_card) * 45)
    all_card = '\r'.join(operator.add(operator.add(new_card, had_card), [f"累计共获得{all_time}分钟余剩虚神界内闭关时间!\r"]))
    text += f"抽卡{10 * num}次结果如下：\r"
    text += f"{all_card}5分钟虚神界闭关时间 X{((num * 10) - card)}"
    xiuxian_impart.add_impart_exp_day(all_time, user_id)
    xiuxian_impart.update_impart_wish(wish_count, user_id)
    msg = main_md(msg, text, '传承背包', '传承背包', '继续抽卡', '传承抽卡', '虚神界对决', '虚神界对决', '传承帮助', '传承帮助')
    await re_impart_data(user_id)
    await bot.send(event=event, message=msg)
    await impart_draw_fast.finish()


@impart_back.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_back_(bot: Bot, event: GroupMessageEvent):
    """传承背包"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await impart_back.finish()

    msg = ""

    img_tp = impart_data_json.data_person_list(user_id)
    msg += (f"--道友{user_info['user_name']}的传承物资--\r"
            f"思恋结晶：{impart_data_draw['stone_num']}颗\r"
            f"祈愿结晶：{impart_data_draw['pray_stone_num']}颗\r"
            f"抽卡次数：{impart_data_draw['wish']}/90次\r"
            f"传承卡图数量：{len(img_tp)}/106\r"
            f"余剩虚神界内闭关时间：{impart_data_draw['exp_day']}分钟\r")
    text = (f"--道友{user_info['user_name']}的传承总属性--\r"
            f"攻击提升:{int(impart_data_draw['impart_atk_per'] * 100)}%\r"
            f"气血提升:{int(impart_data_draw['impart_hp_per'] * 100)}%\r"
            f"真元提升:{int(impart_data_draw['impart_mp_per'] * 100)}%\r"
            f"会心提升：{int(impart_data_draw['impart_know_per'] * 100)}%\r"
            f"会心伤害提升：{int(impart_data_draw['impart_burst_per'] * 100)}%\r"
            f"闭关经验提升：{int(impart_data_draw['impart_exp_up'] * 100)}%\r"
            f"炼丹收获数量提升：{impart_data_draw['impart_mix_per']}颗\r"
            f"灵田收取数量提升：{impart_data_draw['impart_reap_per']}颗\r"
            f"每日双修次数提升：{impart_data_draw['impart_two_exp']}次\r"
            f"boss战攻击提升:{int(impart_data_draw['boss_atk'] * 100)}%\r"
            f"道友拥有的传承卡片如下:")
    img_tp = impart_data_json.data_person_list(user_id)

    text += "\r".join(img_tp)
    msg = main_md(msg, text, '传承卡图 【卡图名称】', '传承卡图', '传承抽卡', '传承抽卡', '虚神界对决', '虚神界对决', '传承帮助', '传承帮助')
    await bot.send(event=event, message=msg)
    await impart_back.finish()


@re_impart_load.handle(parameterless=[Cooldown(at_sender=False)])
async def re_impart_load_(bot: Bot, event: GroupMessageEvent):
    """加载传承数据"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await re_impart_load.finish()
    # 更新传承数据
    info = await re_impart_data(user_id)
    if info:
        msg = f"传承数据加载完成！"
    else:
        msg = f"传承数据加载失败！"
    await bot.send(event=event, message=msg)
    await re_impart_load.finish()


@impart_info.handle(parameterless=[Cooldown(at_sender=False)])
async def impart_info_(bot: Bot, event: GroupMessageEvent):
    """传承信息"""

    _, user_info, _ = check_user(event)

    user_id = user_info['user_id']
    impart_data_draw = await impart_check(user_id)
    if impart_data_draw is None:
        msg = f"发生未知错误，多次尝试无果请找晓楠！"
        await bot.send(event=event, message=msg)
        await impart_info.finish()
    img_tp = impart_data_json.data_person_list(user_id)
    msg = f"""--道友{user_info['user_name']}的传承物资--
思恋结晶：{impart_data_draw['stone_num']}颗
抽卡次数：{impart_data_draw['wish']}/90次
传承卡图数量：{len(img_tp)}/106
余剩虚神界内闭关时间：{impart_data_draw['exp_day']}分钟
    """
    await bot.send(event=event, message=msg)
    await impart_info.finish()
