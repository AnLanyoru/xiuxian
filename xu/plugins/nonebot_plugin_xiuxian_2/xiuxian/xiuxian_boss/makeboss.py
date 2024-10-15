import random
from pathlib import Path
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from .bossconfig import get_boss_config
import json

config = get_boss_config()
JINGJIEEXP = {  # 数值为中期和圆满的平均值
    "炼体境": [1000, 2000, 3000],
    "感气境": [6000, 8000.10000],
    "引气境": [30000, 60000, 90000],
    "凝气境": [144000, 160000, 176000],
    "聚元境": [352000, 284000, 416000],
    "归元境": [832000, 896000, 960000],
    "通玄境": [1920000, 2048000, 2176000],
    "踏虚境": [4352000, 4608000, 4864000],
    "天人境": [9728000, 12348000, 14968000],
    "悟道境": [30968000, 35968000, 40968000],
    "炼神境": [60968000, 70968000, 80968000],
    "逆虚境": [120968000, 140968000, 160968000],
    "合道境": [321936000, 450710400, 579484800],
    "虚劫境": [1158969600, 1622557440, 2086145280],
    "羽化境": [4172290560, 5841206784, 7510123008],
    "登仙境": [15020246016, 21028344422, 27036442828],
    "凡仙境": [54072885657, 75702039920, 97331194180],
    "地仙境": [194662388360, 272527343704, 350392299048],
    "玄仙境": [1550392299048, 1850392299048, 2150392299048],
    "金仙境": [10751961495240, 15039229904800, 42150392299048]
}

jinjie_list = [k for k, v in JINGJIEEXP.items()]
sql_message = XiuxianDateManage()  # sql类

def get_boss_jinjie_dict():
    CONFIGJSONPATH = Path() / "data" / "xiuxian" / "境界.json"
    with open(CONFIGJSONPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    temp_dict = {}
    data = json.loads(data)
    for k, v in data.items():
        temp_dict[k] = v['exp']
    return temp_dict


def get_boss_exp(boss_jj):
    if boss_jj in JINGJIEEXP:
        bossexp = random.choice(JINGJIEEXP[boss_jj])
        bossinfo = {
            '气血': bossexp * config["Boss倍率"]["气血"],
            '总血量': bossexp * config["Boss倍率"]["气血"],
            '真元': bossexp * config["Boss倍率"]["真元"],
            '攻击': int(bossexp * config["Boss倍率"]["攻击"])
        }
        return bossinfo
    else:
        return None


def createboss():
    top_user_info = sql_message.get_top1_user()
    top_user_level = top_user_info['level']
    if len(top_user_level) == 5:
        level = top_user_level[:3] 
    elif len(top_user_level) == 4: # 对求道者判断
        level = "炼体境"

    boss_jj = random.choice(jinjie_list[:jinjie_list.index(level) + 1])
    bossinfo = get_boss_exp(boss_jj)
    bossinfo['name'] = random.choice(config["Boss名字"])
    bossinfo['jj'] = boss_jj
    bossinfo['stone'] = random.choice(config["Boss灵石"][boss_jj])
    return bossinfo


def createboss_jj(boss_jj, boss_name=None):
    bossinfo = get_boss_exp(boss_jj)
    if bossinfo:
        bossinfo['name'] = boss_name if boss_name else random.choice(config["Boss名字"])
        bossinfo['jj'] = boss_jj
        bossinfo['stone'] = random.choice(config["Boss灵石"][boss_jj])
        return bossinfo
    else:
        return None


