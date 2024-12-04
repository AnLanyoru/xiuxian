from ..xiuxian_sect import get_config
from ..xiuxian_utils.clean_utils import help_md
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage
)
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent
)
from ..xiuxian_utils.lay_out import Cooldown
from ..xiuxian_utils.data_source import jsondata
from ..xiuxian_config import XiuConfig

sql_message = XiuxianDateManage()  # sql类
config = get_config()
LEVLECOST = config["LEVLECOST"]
userstask = {}

help_in = on_command("修仙帮助", aliases={"/菜单", "/修仙帮助"}, priority=12, permission=GROUP, block=True)
help_newer = on_command("新手", aliases={"怎么玩", "教", "玩法", "不明白", "教程", "修仙新手", "刚玩",
                                              "怎么弄", "干什么", "玩什么", "新手", "有什么", "玩不来", "/新手教程",
                                              "不会", "不懂", "帮助"}, priority=12, permission=GROUP, block=True)
sect_help = on_command("宗门帮助", aliases={"宗门", "工会"}, priority=21, permission=GROUP, block=True)
sect_help_control = on_command("管理宗门", aliases={"宗门管理"}, priority=6, permission=GROUP, block=True)
sect_help_owner = on_command("宗主必看", aliases={"宗主"}, priority=20, permission=GROUP, block=True)
sect_help_member = on_command("成员必看", aliases={"宗门指令"}, priority=20, permission=GROUP, block=True)
buff_help = on_command("功法帮助", aliases={"功法", "技能", "神通"}, priority=2, permission=GROUP, block=True)
buff_home = on_command("洞天福地帮助", aliases={"灵田帮助", "灵田", "洞天福地"}, priority=20, permission=GROUP, block=True)
store_help = on_command("灵宝楼帮助", aliases={"灵宝楼", "个人摊位", "个人摊位帮助"}, priority=20, permission=GROUP, block=True)
tower_help = on_command("位面挑战帮助", aliases={'挑战'}, priority=21, permission=GROUP, block=True)

__xiuxian_notes__ = f"""
————修仙帮助————
新手教程：
 - 获取修仙新手教程
重入仙途:
 - 更换灵根,每次{XiuConfig().remake}灵石
改头换面:
 - 修改你的道号
突破:
 - 修为足够后,可突破境界
灵石修炼：
 - 使用灵石进行快速修炼，不要贪多哦
排行榜:
 - 查看诸天万界修仙排行榜
日志记录
 - 获取最近10次重要日常操作的记录
我的状态:
 -查看当前状态
————更多玩法帮助
灵宝楼帮助|
灵庄帮助|宗门帮助|背包帮助|
灵田帮助|功法帮助|传承帮助|
——tips——
官方群914556251
""".strip()


__sect_help__ = f"""
\r————宗门帮助————
1：我的宗门
 - 查看当前所处宗门信息
2：宗门列表
 - 查看所有宗门列表
3：创建宗门
 - 创建宗门，需求：{XiuConfig().sect_create_cost}灵石，需求境界{XiuConfig().sect_min_level}
4：加入宗门
 - 加入一个宗门,需要带上宗门id
5：管理宗门
 - 获取所有宗门管理指令
6：宗门指令
 - 查看所有宗门普通成员指令
7：宗主指令
 - 查看所有宗主指令
——tips——
官方群914556251

""".strip()


__buff_help__ = f"""
——功法帮助——
1：我的功法:
 - 查看自身功法以及背包内的所有功法信息
2：切磋:
 - at对应人员,不会消耗气血
3：抑制黑暗动乱:
 - 清除修为浮点数
4：我的双修次数:
 - 查看剩余双修次数
——tips——
官方群914556251
""".strip()


__home_help__ = f"""
——洞天福地帮助——
1：洞天福地购买
 - 购买洞天福地
2：洞天福地查看
 - 查看自己的洞天福地
3：洞天福地改名
 - 随机修改自己洞天福地的名字
4：灵田开垦
 - 提升灵田的等级,提高灵田结算的药材数量
5：灵田收取
 - 收取灵田内生长的药材
——tips——
灵田基础成长时间为47小时
""".strip()


__store_help__ = f"""
——灵宝楼帮助——
灵宝楼指令大全
1：灵宝楼求购 物品 价格 数量
 - 向灵宝楼提交求购物品申请
2：灵宝楼出售 物品 道号
 - 向有求购的玩家出售对应物品
 - 不输 道号 会按市场最高价出售
3：灵宝楼求购查看 物品
 - 查看对应物品的最高求购价
4：我的灵宝楼求购
 - 查看自身灵宝楼求购
5：灵宝楼取灵石 数量
 - 从灵宝楼中取出灵石，收取20%手续费
6：取消求购 物品名称
 - 下架你的求购物品
——tips——
官方群914556251
""".strip()


__tower_help__ = f"""
——位面挑战指令帮助——
1：进入挑战之地
 - 在存在挑战副本的位置使用
   可以进入挑战之地开始挑战
   凡界：灵虚古境(前往3)
   灵界：紫霄神渊(前往19)
2：查看挑战
 - 查看当前挑战信息
3：开始挑战
 - 进行本层次挑战
4：离开挑战之地
 - 停止对挑战之地的探索
5：挑战商店
 - 消耗挑战积分兑换物品
6：挑战之地规则详情
 - 获取位面挑战的详情规则
7：结算挑战积分
 - 获取本周抵达最高层的对应积分
——tips——
官方群914556251
""".strip()


@help_in.handle(parameterless=[Cooldown(at_sender=False)])
async def help_in_(bot: Bot, event: GroupMessageEvent):
    """修仙帮助"""
    msg = help_md("102368631_1733157336", "测试中")
    await bot.send(event=event, message=msg)
    await help_in.finish()


@help_newer.handle(parameterless=[Cooldown(at_sender=False)])
async def help_in_(bot: Bot, event: GroupMessageEvent):
    """修仙新手帮助"""
    msg = help_md("102368631_1733157618", "测试中")
    await bot.send(event=event, message=msg)
    await help_newer.finish()


@sect_help.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_(bot: Bot, event: GroupMessageEvent):
    """宗门帮助"""
    msg = __sect_help__
    await bot.send(event=event, message=msg)
    await sect_help.finish()


@sect_help_control.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_control_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    msg = f"""\r———宗门管理菜单———
1：宗门职位变更
 - 长老以上职位可以改变宗门成员的职位等级
 - 【0 1 2 3 4】分别对应【宗主 长老 亲传 内门 外门】
 - (外门弟子无法获得宗门修炼资源)
2：踢出宗门
 - 踢出对应宗门成员,需要输入正确的道号
3：宗门周贡检查
检查宗门成员周贡
———tips———
官方群914556251
每日{config["发放宗门资材"]["时间"]}点发放{config["发放宗门资材"]["倍率"]}倍对应宗门建设度的资材
"""
    await bot.send(event=event, message=msg)
    await sect_help_control.finish()


@sect_help_owner.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_owner_(bot: Bot, event: GroupMessageEvent):
    """宗主帮助"""
    msg = f"""\r———宗主菜单———
1：宗门职位变更
 - 宗主可以改变宗门成员的职位等级
 - 【0 1 2 3 4】分别对应【宗主 长老 亲传 内门 外门】
 - (外门弟子无法获得宗门修炼资源)
2：踢出宗门
 - 踢出对应宗门成员,需要输入正确的道号
3：建设宗门丹房
 - 建设宗门丹房，可以让每个宗门成员每日领取丹药
4：宗门搜寻功法|神通:
 - 宗主可消耗宗门资材和宗门灵石来搜寻10次功法或者神通
5：宗门成员查看
 - 查看所在宗门的成员信息
6：宗主传位
 - 宗主可以传位宗门成员
7：宗门改名
 - 宗主可以消耗宗门资源改变宗门名称
8：宗门周贡检查
检查宗门成员周贡
———tips———
官方群914556251
每日{config["发放宗门资材"]["时间"]}点发放{config["发放宗门资材"]["倍率"]}倍对应宗门建设度的资材
"""
    await bot.send(event=event, message=msg)
    await sect_help_owner.finish()


@sect_help_member.handle(parameterless=[Cooldown(at_sender=False)])
async def sect_help_member_(bot: Bot, event: GroupMessageEvent):
    """宗门管理帮助"""
    msg = f"""\r————宗门指令帮助————
1：我的宗门
 - 查看当前所处宗门信息
2：宗门捐献
 - 建设宗门，提高宗门建设度
 - 每{config["等级建设度"]}建设度会提高1级攻击修炼等级上限
3：升级攻击修炼
 - 升级道友的攻击修炼等级
 - 每级修炼等级提升4%攻击力,后可以接升级等级
 - 需要亲传弟子
4：宗门任务接取
 - 接取宗门任务，可以增加宗门建设度和资材
 - 每日上限：{config["每日宗门任务次上限"]}次
5：宗门任务完成
 - 完成所接取的宗门任务
 - 完成间隔时间：{config["宗门任务完成cd"]}秒
6：宗门任务刷新
 - 刷新当前所接取的宗门任务
 - 刷新间隔时间：{config["宗门任务刷新cd"]}秒
7：学习宗门功法|神通
 - 宗门亲传弟子可消耗宗门资材来学习宗门功法或者神通，后接功法名称
8：宗门功法查看
 - 查看当前宗门已有的功法
9：宗门成员查看
 - 查看所在宗门的成员信息
10：宗门丹药领取
 - 领取宗门丹药，需要内门弟子且1000万宗门贡献
11：退出宗门
 - 退出当前宗门
——tips——
宗主|长老|亲传弟子|内门弟子|外门弟子
宗门任务获得修为上限分别为：
{jsondata.sect_config_data()[str(0)]["max_exp"]}|{jsondata.sect_config_data()[str(1)]["max_exp"]}|{jsondata.sect_config_data()[str(2)]["max_exp"]}|{jsondata.sect_config_data()[str(3)]["max_exp"]}|{jsondata.sect_config_data()[str(4)]["max_exp"]}
"""
    await bot.send(event=event, message=msg)
    await sect_help_member.finish()


@buff_help.handle(parameterless=[Cooldown(at_sender=False)])
async def buff_help_(bot: Bot, event: GroupMessageEvent):
    """功法帮助"""
    msg = __buff_help__
    await bot.send(event=event, message=msg)
    await buff_help.finish()


@buff_home.handle(parameterless=[Cooldown(at_sender=False)])
async def buff_home_(bot: Bot, event: GroupMessageEvent):
    """灵田帮助"""
    msg = __home_help__
    await bot.send(event=event, message=msg)
    await buff_home.finish()


@store_help.handle(parameterless=[Cooldown(at_sender=False)])
async def store_help_(bot: Bot, event: GroupMessageEvent):
    """帮助"""
    msg = __store_help__
    await bot.send(event=event, message=msg)
    await store_help.finish()


@tower_help.handle(parameterless=[Cooldown(at_sender=False)])
async def tower_help_(bot: Bot, event: GroupMessageEvent):
    """帮助"""
    msg = __tower_help__
    await bot.send(event=event, message=msg)
    await tower_help.finish()
