import os
import io
import asyncio
import json
import math
import datetime
import re

import unicodedata

from .clean_utils import get_num_from_str
from .xiuxian2_handle import XiuxianDateManage
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    MessageSegment
)
from nonebot.params import Depends
from io import BytesIO
from ..xiuxian_config import XiuConfig
from PIL import Image, ImageDraw, ImageFont
from wcwidth import wcwidth
from nonebot.adapters import MessageSegment
from nonebot.adapters.onebot.v11 import MessageSegment
from .data_source import jsondata
from pathlib import Path
from base64 import b64encode
from ..xiuxian_place import Place, PLAYERSDATA

sql_message = XiuxianDateManage()  # sql类
boss_img_path = Path() / "data" / "xiuxian" / "boss_img"


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        if isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, float):
            return float(obj)
        else:
            return super(MyEncoder, self).default(obj)


def read_move_data(user_id):
    user_id = str(user_id)
    FILEPATH = PLAYERSDATA / user_id / "moveinfo.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def check_user_type(user_id, need_type):
    """
    说明: 匹配用户状态，返回是否状态一致
    :param user_id: type = str 用户ID
    :param need_type: type = int 需求状态 -1为移动中  0为空闲中  1为闭关中  2为悬赏令中
    :returns: isType: 是否一致 ， msg: 消息体
    """
    isType = False
    msg = ''
    user_cd_message = sql_message.get_user_cd(user_id)
    if user_cd_message is None:
        user_type = 0
    else:
        user_type = user_cd_message['type']
    # 此处结算移动
    if user_type == need_type:  # 状态一致
        isType = True
    else:
        if user_type == 1:
            msg = "道友现在在闭关呢，小心走火入魔！"

        elif user_type == 2:
            msg = "道友现在在做悬赏令呢，小心走火入魔！"

        elif user_type == 3:
            msg = "道友现在正在秘境中，分身乏术！"

        elif user_type == 4:
            msg = "道友正在修炼中，请抱元守一，聚气凝神，勿要分心！\n若是调用修炼看到此消息，道友大概率需要：\n【停止修炼】！！！"

        elif user_type == 5:
            msg = "道友正在虚神界修炼中，请抱元守一，聚气凝神，勿要分心！"

        elif user_type == 0:
            msg = "道友现在什么都没干呢~"

        elif user_type == -1:
            # 前面添加赶路检测
            user_cd_message = sql_message.get_user_cd(user_id)
            work_time = datetime.datetime.strptime(
                user_cd_message['create_time'], "%Y-%m-%d %H:%M:%S.%f"
            )
            pass_time = (datetime.datetime.now() - work_time).seconds // 60  # 时长计算
            move_info = read_move_data(user_id)
            need_time = move_info["need_time"]
            place_name = Place().get_place_name(move_info["to_id"])
            if pass_time < need_time:
                last_time = math.ceil(need_time - pass_time)
                msg = f"道友现在正在赶往【{place_name}】中！预计还有{last_time}分钟到达目的地！！"
            else:  # 移动结算逻辑
                sql_message.do_work(user_id, 0)
                place_id = move_info["to_id"]
                Place().set_now_place_id(user_id, place_id)
                msg = f"道友成功抵达【{place_name}】！！！"

    return isType, msg


def check_user(event: GroupMessageEvent):
    """
    判断用户信息是否存在
    :返回参数:
      * `isUser: 是否存在
      * `user_info: 用户
      * `msg: 消息体
    """
    user_id = event.get_user_id()
    user_info = sql_message.get_user_info_with_id(user_id)

    return True, user_info, ''


class Txt2Img:
    """文字转图片"""

    def __init__(self, size=32):
        self.font = str(jsondata.FONT_FILE)
        self.font_size = int(size)
        self.use_font = ImageFont.truetype(font=self.font, size=self.font_size)
        self.upper_size = 30
        self.below_size = 30
        self.left_size = 40
        self.right_size = 55
        self.padding = 12
        self.img_width = 780
        self.black_clor = (255, 255, 255)
        self.line_num = 0

        self.user_font_size = int(size * 1.5)
        self.lrc_font_size = int(size)
        self.font_family = str(jsondata.FONT_FILE)
        self.share_img_width = 1080
        self.line_space = int(size)
        self.lrc_line_space = int(size / 2)

    # 预处理
    def prepare(self, text, scale):
        text = unicodedata.normalize("NFKC", text)
        if scale:
            max_text_len = self.img_width - self.left_size - self.right_size
        else:
            max_text_len = 1080 - self.left_size - self.right_size
        use_font = self.use_font
        line_num = self.line_num
        text_len = 0
        text_new = ""
        for x in text:
            text_new += x
            text_len += use_font.getlength(x)
            if x == "\n":
                text_len = 0
            if text_len >= max_text_len:
                text_len = 0
                text_new += "\n"
        text_new = text_new.replace("\n\n", "\n")
        text_new = text_new.rstrip()
        line_num = line_num + text_new.count("\n")
        return text_new, line_num

    def sync_draw_to(self, text, boss_name="", scale=True):
        font_size = self.font_size
        black_clor = self.black_clor
        upper_size = self.upper_size
        below_size = self.below_size
        left_size = self.left_size
        padding = self.padding
        img_width = self.img_width
        use_font = self.use_font
        text, line_num = self.prepare(text=text, scale=scale)
        if scale:
            if line_num < 5:
                blank_space = int(5 - line_num)
                line_num = 5
                text += "\n"
                for k in range(blank_space):
                    text += "(^ ᵕ ^)\n"
            else:
                line_num = line_num
        else:
            img_width = 1080
            line_num = line_num
        img_hight = int(upper_size + below_size + font_size * (line_num + 1) + padding * line_num)
        out_img = Image.new(mode="RGB", size=(img_width, img_hight),
                            color=black_clor)
        draw = ImageDraw.Draw(out_img, "RGBA")

        # 设置
        banner_size = 12
        border_color = (220, 211, 196)
        out_padding = 15
        mi_img = Image.open(jsondata.BACKGROUND_FILE)
        mi_banner = Image.open(jsondata.BANNER_FILE).resize(
            (banner_size, banner_size), resample=3
        )

        # 添加背景
        for x in range(int(math.ceil(img_hight / 100))):
            out_img.paste(mi_img, (0, x * 100))

        # 添加边框
        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle(
                    (rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i),
                    outline=border_color,
                )

        draw_rectangle(
            draw, (out_padding, out_padding, img_width - out_padding, img_hight - out_padding), 2
        )

        # 添加banner
        out_img.paste(mi_banner, (out_padding, out_padding))
        out_img.paste(
            mi_banner.transpose(Image.FLIP_TOP_BOTTOM),
            (out_padding, img_hight - out_padding - banner_size + 1),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT),
            (img_width - out_padding - banner_size + 1, out_padding),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM),
            (img_width - out_padding - banner_size + 1, img_hight - out_padding - banner_size + 1),
        )

        # 绘制文字
        draw.text(
            (left_size, upper_size),
            text,
            font=use_font,
            fill=(125, 101, 89),
            spacing=padding,
        )
        # 贴boss图
        if boss_name:
            boss_img_path = jsondata.BOSS_IMG / f"{boss_name}.png"
            if os.path.exists(boss_img_path):
                boss_img = Image.open(boss_img_path)
                base_cc = boss_img.height / img_hight
                boss_img_w = int(boss_img.width / base_cc)
                boss_img_h = int(boss_img.height / base_cc)
                boss_img = boss_img.resize((int(boss_img_w), int(boss_img_h)), Image.Resampling.LANCZOS)
                out_img.paste(
                    boss_img,
                    (int(img_width - boss_img_w), int(img_hight - boss_img_h)),
                    boss_img
                )
        if XiuConfig().img_send_type == "io":
            return out_img
        elif XiuConfig().img_send_type == "base64":
            return self.img2b64(out_img)

    def img2b64(self, out_img) -> str:
        """ 将图片转换为base64 """
        buf = BytesIO()
        out_img.save(buf, format="PNG")
        base64_str = "base64://" + b64encode(buf.getvalue()).decode()
        return base64_str

    async def io_draw_to(self, text, boss_name="", scale=True):  # draw_to
        loop = asyncio.get_running_loop()
        out_img = await loop.run_in_executor(None, self.sync_draw_to, text, boss_name, scale)
        return await loop.run_in_executor(None, self.save_image_with_compression, out_img)

    async def save(self, title, lrc):
        """保存图片,涉及title时使用"""
        border_color = (220, 211, 196)
        text_color = (125, 101, 89)

        out_padding = 30
        padding = 45
        banner_size = 20

        user_font = ImageFont.truetype(self.font_family, self.user_font_size)
        lyric_font = ImageFont.truetype(self.font_family, self.lrc_font_size)

        if title == ' ':
            title = ''

        lrc = self.wrap(lrc)

        if lrc.find("\n") > -1:
            lrc_rows = len(lrc.split("\n"))
        else:
            lrc_rows = 1

        w = self.share_img_width

        if title:
            inner_h = (
                    padding * 2
                    + self.user_font_size
                    + self.line_space
                    + self.lrc_font_size * lrc_rows
                    + (lrc_rows - 1) * self.lrc_line_space
            )
        else:
            inner_h = (
                    padding * 2
                    + self.lrc_font_size * lrc_rows
                    + (lrc_rows - 1) * self.lrc_line_space
            )

        h = out_padding * 2 + inner_h

        out_img = Image.new(mode="RGB", size=(w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        mi_img = Image.open(jsondata.BACKGROUND_FILE)
        mi_banner = Image.open(jsondata.BANNER_FILE).resize(
            (banner_size, banner_size), resample=3
        )

        # add background
        for x in range(int(math.ceil(h / 100))):
            out_img.paste(mi_img, (0, x * 100))

        # add border
        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle(
                    (rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i),
                    outline=border_color,
                )

        draw_rectangle(
            draw, (out_padding, out_padding, w - out_padding, h - out_padding), 2
        )

        # add banner
        out_img.paste(mi_banner, (out_padding, out_padding))
        out_img.paste(
            mi_banner.transpose(Image.FLIP_TOP_BOTTOM),
            (out_padding, h - out_padding - banner_size + 1),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT),
            (w - out_padding - banner_size + 1, out_padding),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM),
            (w - out_padding - banner_size + 1, h - out_padding - banner_size + 1),
        )

        if title:
            tmp_img = Image.new("RGB", (1, 1))
            tmp_draw = ImageDraw.Draw(tmp_img)
            user_bbox = tmp_draw.textbbox((0, 0), title, font=user_font, spacing=self.line_space)
            # 四元组(left, top, right, bottom)
            user_w = user_bbox[2] - user_bbox[0]  # 宽度 = right - left
            user_h = user_bbox[3] - user_bbox[1]
            draw.text(
                ((w - user_w) // 2, out_padding + padding),
                title,
                font=user_font,
                fill=text_color,
                spacing=self.line_space,
            )
            draw.text(
                (
                    out_padding + padding,
                    out_padding + padding + self.user_font_size + self.line_space,
                ),
                lrc,
                font=lyric_font,
                fill=text_color,
                spacing=self.lrc_line_space,
            )
        else:
            draw.text(
                (out_padding + padding, out_padding + padding),
                lrc,
                font=lyric_font,
                fill=text_color,
                spacing=self.lrc_line_space,
            )
        if XiuConfig().img_send_type == "io":
            buf = BytesIO()
            if XiuConfig().img_type == "webp":
                out_img.save(buf, format="WebP")
            elif XiuConfig().img_type == "jpeg":
                out_img.save(buf, format="JPEG")
            buf.seek(0)
            return buf
        elif XiuConfig().img_send_type == "base64":
            return self.img2b64(out_img)

    def save_image_with_compression(self, out_img):
        """对传入图片进行压缩"""
        img_byte_arr = io.BytesIO()
        compression_quality = 100 - XiuConfig().img_compression_limit  # 质量从100到0
        if not (0 <= XiuConfig().img_compression_limit <= 100):
            compression_quality = 0

        if XiuConfig().img_type == "webp":
            out_img.save(img_byte_arr, format="WebP", quality=compression_quality)
        elif XiuConfig().img_type == "jpeg":
            out_img.save(img_byte_arr, format="JPEG", quality=compression_quality)
        else:
            out_img.save(img_byte_arr, format="WebP", quality=compression_quality)
        img_byte_arr.seek(0)
        return img_byte_arr

    def wrap(self, string):
        max_width = int(1850 / self.lrc_font_size)
        temp_len = 0
        result = ''
        for ch in string:
            result += ch
            temp_len += wcwidth(ch)
            if ch == '\n':
                temp_len = 0
            if temp_len >= max_width:
                temp_len = 0
                result += '\n'
        result = result.rstrip()
        return result


async def get_msg_pic(msg, boss_name="", scale=True):
    img = Txt2Img()
    if XiuConfig().img_send_type == "io":
        pic = await img.io_draw_to(msg, boss_name, scale)
    elif XiuConfig().img_send_type == "base64":
        pic = img.sync_draw_to(msg, boss_name, scale)
    return pic


async def send_msg_handler(bot, event, *args):
    """
    统一消息发送处理器
    :param bot: 机器人实例
    :param event: 事件对象
    :param args: 消息内容列表
    """

    if XiuConfig().merge_forward_send == 1:
        if len(args) == 3:
            name, uin, msgs = args
            messages = [{"type": "node", "data": {"name": name, "uin": uin, "content": msg}} for msg in msgs]
            if isinstance(event, GroupMessageEvent):
                await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=messages)
            else:
                await bot.call_api("send_private_forward_msg", user_id=event.user_id, messages=messages)
        elif len(args) == 1 and isinstance(args[0], list):
            messages = args[0]
            if isinstance(event, GroupMessageEvent):
                await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=messages)
            else:
                await bot.call_api("send_private_forward_msg", user_id=event.user_id, messages=messages)
        else:
            raise ValueError("参数数量或类型不匹配")
    elif XiuConfig().merge_forward_send == 2:  # 合并作为文本发送
        if len(args) == 3:
            name, uin, msgs = args
            messages = '\n'.join(msgs)
            if isinstance(event, GroupMessageEvent):
                await bot.send(event=event, message=messages)
            else:
                await bot.send_private_msg(user_id=event.user_id, message=messages)
        elif len(args) == 1 and isinstance(args[0], list):
            messages = args[0]
            try:
                messages = '\n'.join([str(msg['data']['content']) for msg in messages])
            except TypeError:
                messages = '\n'.join([str(msg) for msg in messages])
            if isinstance(event, GroupMessageEvent):
                await bot.send(event=event, message=messages)
            else:
                await bot.send_private_msg(user_id=event.user_id, message=messages)
        else:
            raise ValueError("参数数量或类型不匹配")
    else:
        if len(args) == 3:
            name, uin, msgs = args
            img = Txt2Img()
            messages = '\n'.join(msgs)
            if XiuConfig().img_send_type == "io":
                img_data = await img.io_draw_to(messages)
            elif XiuConfig().img_send_type == "base64":
                img_data = img.sync_draw_to(messages)
            if isinstance(event, GroupMessageEvent):
                await bot.send(event=event, message=MessageSegment.image(img_data))
            else:
                await bot.send_private_msg(user_id=event.user_id, message=MessageSegment.image(img_data))

        elif len(args) == 1 and isinstance(args[0], list):
            messages = args[0]
            img = Txt2Img()
            messages = '\n'.join([str(msg['data']['content']) for msg in messages])
            if XiuConfig().img_send_type == "io":
                img_data = await img.io_draw_to(messages)
            elif XiuConfig().img_send_type == "base64":
                img_data = img.sync_draw_to(messages)
            if isinstance(event, GroupMessageEvent):
                await bot.send(event=event, message=MessageSegment.image(img_data))
            else:
                await bot.send_private_msg(user_id=event.user_id, message=MessageSegment.image(img_data))
        else:
            raise ValueError("参数数量或类型不匹配")


def CommandObjectID() -> int:
    """
    根据消息事件的类型获取对象id
    私聊->用户id
    群聊->群id
    频道->子频道id
    :return: 对象id
    """

    def _event_id(event):
        if event.message_type == 'private':
            return event.user_id
        elif event.message_type == 'group':
            return event.group_id
        elif event.message_type == 'guild':
            return event.channel_id

    return Depends(_event_id)


def number_to(num):
    """
    递归实现，精确为最大单位值 + 小数点后一位
    处理科学计数法表示的数值
    """

    # 处理列表类数据
    if num:
        pass
    else:
        # 打回
        return "无"
    if type(num) == str:
        hf = ""
        num = num.split("、")
        final_num = ""
        for num_per in num:
            # 对列表型数值每个处理输出到新list
            # 处理字符串输入
            if type(num_per) != int:
                # 处理坑爹的伤害列表
                if num_per[-2:] == "伤害":
                    num_per = num_per[:-2]
                    hf = "点伤害"
                num_per = int(num_per)
            # 处理负数输出
            fh = ""
            if num_per < 0:
                fh = "-"
                num_per = abs(num_per)

            def strofsize(num_per, level):
                if level >= 29:
                    return num_per, level
                elif num_per >= 10000:
                    num_per /= 10000
                    level += 1
                    return strofsize(num_per, level)
                else:
                    return num_per, level

            units = ['', '万', '亿', '万亿', '兆', '万兆', '亿兆', '万亿兆', '京', '万京', '亿京', '万亿京', '兆京',
                     '万兆京', '亿兆京', '万亿兆京', '垓', '万垓', '亿垓', '万亿垓',
                     '兆垓', '万兆垓', '亿兆垓', '万亿兆垓', '京垓', '万京垓',
                     '亿京垓', '万亿京垓', '兆京垓', '万兆京垓']
            # 处理科学计数法
            if "e" in str(num_per):
                num_per = float(f"{num_per  :.1f}")
            num_per, level = strofsize(num_per, 0)
            if level >= len(units):
                level = len(units) - 1
            final_num += "、" + f"{fh}{round(num_per, 1)}{units[level]}" + hf
        return final_num[1:]
    else:
        # 处理字符串输入
        if type(num) == str:
            # 处理坑爹的伤害列表
            if num[-2:] == "伤害":
                num = num[:-2]
            num = int(num)
        # 处理负数输出
        fh = ""
        if num < 0:
            fh = "-"
            num = abs(num)

        def strofsize(num, level):
            if level >= 29:
                return num, level
            elif num >= 10000:
                num /= 10000
                level += 1
                return strofsize(num, level)
            else:
                return num, level

        units = ['', '万', '亿', '万亿', '兆', '万兆', '亿兆', '万亿兆', '京', '万京', '亿京', '万亿京', '兆京',
                 '万兆京', '亿兆京', '万亿兆京', '垓', '万垓', '亿垓', '万亿垓',
                 '兆垓', '万兆垓', '亿兆垓', '万亿兆垓', '京垓', '万京垓',
                 '亿京垓', '万亿京垓', '兆京垓', '万兆京垓']
        # 处理科学计数法
        if "e" in str(num):
            num = float(f"{num:.1f}")
        num, level = strofsize(num, 0)
        if level >= len(units):
            level = len(units) - 1
        final_num = f"{fh}{round(num, 1)}{units[level]}"
    return final_num


def get_id_from_str(msg: str):
    """
    将消息中的首个字符组合转换为
    :param msg: 从args中获取的消息字符串
    :return: 如果有该用户，返回用户ID，若无，返回None
    """
    user_name = re.findall(r"[\u4e00-\u9fa5_a-zA-Z]+", msg)
    if user_name:
        user_id = sql_message.get_user_id(user_name[0])
    else:
        user_id = None
    return user_id


def get_strs_from_str(msg: str) -> list:
    """
    从消息字符串中获取字符列表
    :param msg: 从args中获取的消息字符串
    :return: 提取到的字符列表
    """
    strs = re.findall(r"[\u4e00-\u9fa5_a-zA-Z]+", msg)
    return strs

async def pic_msg_format(msg, event):
    user_name = (
        event.sender.card if event.sender.card else event.sender.nickname
    )
    result = "@" + user_name + "\n" + msg
    return result
