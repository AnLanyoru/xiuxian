from io import BytesIO
from pathlib import Path
from typing import Union
from base64 import b64encode
from PIL import Image
import cv2
import numpy as np


async def convert_img(
    img: Union[Image.Image, str, Path, bytes], is_base64: bool = True
):
    """
    :说明:
      将PIL.Image对象转换为bytes或者base64格式。
    :参数:
      * img (Image): 图片。
      * is_base64 (bool): 是否转换为base64格式, 不填默认转为bytes。
    :返回:
      * res: bytes对象或base64编码图片。
    """
    if isinstance(img, Image.Image):
        img = img.convert('RGB')
        result_buffer = BytesIO()
        img.save(result_buffer, format='jpeg', quality=100, subsampling=0)
        pic_byte = result_buffer.getvalue()
        img_np = np.frombuffer(pic_byte, np.uint8)
        res = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)
        pic_type='.jpg'
        res = cv2.imencode(pic_type, res, [int(cv2.IMWRITE_JPEG_QUALITY), 80])[1]
        if is_base64:
            res = 'base64://' + b64encode(res).decode()
        return res
    elif isinstance(img, bytes):
        return 'base64://' + b64encode(img).decode()
    else:
        return 'base64://' + b64encode(img).decode()


'''
pip install numpy
pip install opencv-python
'''

def pic_compress(img, target_size=199, quality=90, step=5, pic_type='.jpg'):
    img = img.convert('RGB')
    result_buffer = BytesIO()
    img.save(result_buffer, format='JPEG', quality=80, subsampling=0)
    pic_byte = result_buffer.getvalue()
    img_np = np.frombuffer(pic_byte, np.uint8)
    img_cv = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)

    current_size = len(pic_byte) / 1024
    print("图片压缩前的大小为(KB)：", current_size)
    while current_size > target_size:
        pic_byte = cv2.imencode(pic_type, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), quality])[1]
        if quality - step < 0:
            break
        quality -= step
        current_size = len(pic_byte) / 1024

    return pic_byte

