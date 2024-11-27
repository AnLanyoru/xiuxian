import pickle
import re
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from limit_database import date, LimitData, LimitHandle

DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


def fast_handle():
    now_time = date.today()
    print("欢迎使用快速活动&补偿&限制操作系统\r", "现在是：", now_time, '\r')
    print(
        "请选择你要进行的操作：\r1：操作活动信息\r2：操作补偿信息\r3：操作用户限制信息(making)\r4：进行模拟用户操作(测试用)")
    choice = None
    while choice not in [1, 2, 3, 4]:
        choice = int(input("请选择你要进行的操作:"))
    if choice == 1:
        print("当前已有活动信息：", LimitHandle().get_active_msg())
        print("请选择你要进行的操作：\r1：添加活动\r2：删除活动(制作中)\r3：修改活动(制作中)\r")
        choice = None
        while choice not in [1, 2, 3]:
            choice = int(input())
        if choice == 1:
            active_id = int(input("请输入活动id："))
            active_name = input("请输入活动名称：")
            active_desc = input("请输入活动介绍：")
            active_deadline = int(input("请输入活动持续时间（天）："))
            last_time = now_time.replace(day=now_time.day + active_deadline)
            active_daily = input("活动是否日刷新奖励（y/n）：")
            active_daily = 0 if active_daily == 'n' else 1
            LimitData().active_make(active_id, active_name, active_desc, str(last_time), active_daily)

            if LimitData().get_active_by_id(active_id):
                print('创建活动成功！！！')
            else:
                print("创建活动失败！！")

        pass
    elif choice == 2:
        print("当前已有补偿信息：", LimitHandle().get_offset_list())
        print("请选择你要进行的操作：\r1：添加补偿\r2：删除补偿\r3：修改补偿(制作中)\r4：查询补偿详情信息\r")
        choice = None
        while choice not in [1, 2, 3, 4]:
            choice = int(input("请输入需要进行的操作id：\r"))
        if choice == 1:
            offset_id = int(input("请输入补偿id："))
            offset_name = input("请输入补偿名称：")
            offset_desc = input("请输入补偿介绍：")
            offset_deadline = int(input("请输入补偿持续时间（天）："))
            last_time = now_time + timedelta(days=offset_deadline)
            offset_daily = input("补偿是否日刷新奖励（y/n）：")
            offset_daily = 0 if offset_daily == 'n' else 1

            item_num = int(input("补偿物品种类数量："))
            offset_items = {}
            for n in range(item_num):
                need_item_id = int(input(f"请输入第{n + 1}个补偿物品id:"))
                need_item_num = int(input(f"请输入第{n + 1}个补偿物品数量:"))
                offset_items[need_item_id] = need_item_num
            LimitData().offset_make(offset_id, offset_name, offset_desc, offset_items, str(last_time), offset_daily)

            if LimitData().get_offset_by_id(offset_id):
                print('创建补偿成功！！！')
            else:
                print("创建补偿失败！！")

        elif choice == 2:
            offset_id = int(input("请输入要删除的补偿id："))
            LimitData().offset_del(offset_id)
            if LimitData().get_offset_by_id(offset_id):
                print('删除补偿失败！！！')
            else:
                print("删除补偿成功！！！")


        elif choice == 4:
            offset_id = int(input("请输入你想要查询的补偿id："))
            info = LimitData().get_offset_by_id(offset_id)
            if info:
                print("查询到如下信息：\r" + LimitHandle().change_offset_info_to_msg(info))
            else:
                print("没有相关补偿信息！！")
        pass
    elif choice == 4:
        user_id = int(input("请输入模拟用户id："))
        print("当前用户限制词典：", LimitData().get_limit_by_user_id(user_id))
        print("项目id总览(施工中略显寒酸)", LimitHandle().keymap)
        choice_type = None
        project_type = 0
        while choice_type is None:
            project_type = int(input("请输入要模拟的项目id：\r1-7观察总表\r"))
            choice_type = LimitHandle().keymap.get(project_type)
        if project_type < 6:
            project_value = int(input("请输入要模拟的项目值：\r"))
            project_mode = int(input("请输入要模拟的项目模式(0加1减)：\r"))
            LimitHandle().update_user_limit(user_id, project_type, project_value, project_mode)
        elif project_type < 7:
            print("当前已有补偿信息：", LimitHandle().get_offset_list())
            offset_id = int(input("请输入要模拟的补偿id："))
            is_pass = LimitHandle().update_user_offset(user_id, offset_id)
            if is_pass:
                print("领取补偿成功")
            else:
                print('领取补偿失败，请勿重复领取')
        print("模拟成功，当前用户限制词典：", LimitData().get_limit_by_user_id(user_id))

        pass

    else:
        pass


if __name__ == '__main__':
    while True:
        fast_handle()
        choice = input("执行结束，任意输入退出")
        if choice:
            break
        else:
            pass
