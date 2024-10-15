import re
import random

from ..xiuxian_sect import get_config
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, OtherSet, BuffJsonDate,
    get_main_info_msg, UserBuffDate, get_sec_msg
)
from nonebot import on_command, on_fullmatch, require
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot.params import CommandArg
from ..xiuxian_utils.data_source import jsondata
from datetime import datetime, timedelta
from ..xiuxian_config import XiuConfig, convert_rank, JsonConfig
from ..xiuxian_utils.utils import (
    check_user, number_to,
    get_msg_pic, send_msg_handler, CommandObjectID,
    Txt2Img, get_num_from_str, get_strs_from_str
)
from ..xiuxian_utils.item_json import Items

items = Items()
sql_message = XiuxianDateManage()  # sql类
config = get_config()
LEVLECOST = config["LEVLECOST"]
userstask = {}

sect_help = on_command("宗门帮助", aliases={"宗门", "工会"}, priority=21, permission=GROUP, block=True)
sect_help_control = on_command("管理宗门", aliases={"宗门管理"}, priority=6, permission=GROUP, block=True)
sect_help_owner = on_command("宗主必看", aliases={"宗主"}, priority=20, permission=GROUP, block=True)
sect_help_member = on_command("成员必看", aliases={"宗门指令"}, priority=20, permission=GROUP, block=True)
buff_help = on_command("功法帮助", aliases={"功法", "技能", "神通"}, priority=2, permission=GROUP, block=True)
buff_home = on_command("洞天福地帮助", aliases={"灵田帮助", "灵田", "洞天福地"}, priority=20, permission=GROUP, block=True)

__sect_help__ = f"""
\n————宗门帮助————
1、我的宗门:
>查看当前所处宗门信息
2、宗门列表:
>查看所有宗门列表
3、创建宗门:
>创建宗门，需求：{XiuConfig().sect_create_cost}灵石，需求境界{XiuConfig().sect_min_level}
4、加入宗门:
>加入一个宗门,需要带上宗门id
5、管理宗门：
>获取所有宗门管理指令
6、宗门指令:
>查看所有宗门普通成员指令
7、宗主指令：
>查看所有宗主指令

""".strip()


__buff_help__ = f"""
——功法帮助——
1、我的功法:
>查看自身功法以及背包内的所有功法信息
2、切磋:
>at对应人员,不会消耗气血
3、抑制黑暗动乱:
>清除修为浮点数
4、我的双修次数:
>查看剩余双修次数
""".strip()


__home_help__ = f"""
——洞天福地帮助——
1、洞天福地购买:
>购买洞天福地
2、洞天福地查看:
>查看自己的洞天福地
3、洞天福地改名：
>随机修改自己洞天福地的名字
4、灵田开垦:
>提升灵田的等级,提高灵田结算的药材数量
5、灵田收取：
>收取灵田内生长的药材
——tips——
灵田基础成长时间为47小时
""".strip()


@sect_help.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_(bot: Bot, event: GroupMessageEvent):
    """宗门帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = __sect_help__
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await sect_help.finish()


@sect_help_control.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_control_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = f"""\n———宗门管理菜单———
1、宗门职位变更:
>长老以上职位可以改变宗门成员的职位等级
>【0 1 2 3 4】分别对应【宗主 长老 亲传 内门 外门】
>(外门弟子无法获得宗门修炼资源)
2、踢出宗门:
>踢出对应宗门成员,需要输入正确的道号
———tips———
每日{config["发放宗门资材"]["时间"]}点发放{config["发放宗门资材"]["倍率"]}倍对应宗门建设度的资材
"""
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await sect_help_control.finish()


@sect_help_owner.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_owner_(bot: Bot, event: GroupMessageEvent):
    """宗主帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = f"""\n———宗主菜单———
1、宗门职位变更:
>宗主可以改变宗门成员的职位等级
>【0 1 2 3 4】分别对应【宗主 长老 亲传 内门 外门】
>(外门弟子无法获得宗门修炼资源)
2、踢出宗门:
>踢出对应宗门成员,需要输入正确的道号
3、建设宗门丹房:
>建设宗门丹房，可以让每个宗门成员每日领取丹药
4、宗门搜寻功法|神通:
>宗主可消耗宗门资材和宗门灵石来搜寻10次功法或者神通
5、宗门成员查看:
>查看所在宗门的成员信息
6、宗主传位:
>宗主可以传位宗门成员
7、宗门改名:
>宗主可以消耗宗门资源改变宗门名称
———tips———
每日{config["发放宗门资材"]["时间"]}点发放{config["发放宗门资材"]["倍率"]}倍对应宗门建设度的资材
"""
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await sect_help_owner.finish()


@sect_help_member.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_member_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = f"""\n————宗门指令帮助————
1、我的宗门:
>查看当前所处宗门信息
2、宗门捐献:
>建设宗门，提高宗门建设度
>每{config["等级建设度"]}建设度会提高1级攻击修炼等级上限
3、升级攻击修炼:
>升级道友的攻击修炼等级
>每级修炼等级提升4%攻击力,后可以接升级等级
>需要亲传弟子
4、宗门任务接取:
>接取宗门任务，可以增加宗门建设度和资材
>每日上限：{config["每日宗门任务次上限"]}次
5、宗门任务完成:
>完成所接取的宗门任务
>完成间隔时间：{config["宗门任务完成cd"]}秒
6、宗门任务刷新:
>刷新当前所接取的宗门任务
>刷新间隔时间：{config["宗门任务刷新cd"]}秒
7、学习宗门功法|神通:
>宗门亲传弟子可消耗宗门资材来学习宗门功法或者神通，后接功法名称
8、宗门功法查看:
>查看当前宗门已有的功法
9、宗门成员查看:
>查看所在宗门的成员信息
10、宗门丹药领取:
>领取宗门丹药，需要内门弟子1000且万宗门贡献
7、退出宗门:
>退出当前宗门
——tips——
宗主|长老|亲传弟子|内门弟子|外门弟子
宗门任务获得修为上限分别为：
{jsondata.sect_config_data()[str(0)]["max_exp"]}|{jsondata.sect_config_data()[str(1)]["max_exp"]}|{jsondata.sect_config_data()[str(2)]["max_exp"]}|{jsondata.sect_config_data()[str(3)]["max_exp"]}|{jsondata.sect_config_data()[str(4)]["max_exp"]}
"""
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await sect_help_member.finish()


@buff_help.handle(parameterless=[Cooldown(at_sender=False)])
async def buff_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """功法帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = __buff_help__
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await buff_help.finish()


@buff_home.handle(parameterless=[Cooldown(at_sender=False)])
async def buff_home_(bot: Bot, event: GroupMessageEvent):
    """灵田帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = __home_help__
    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await buff_home.finish()
