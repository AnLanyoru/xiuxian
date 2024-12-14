import os
import subprocess
from functools import partial
from pathlib import Path

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8')
import execjs
# node.js 原代码作者：阿莱四十二
# python adjust by AnLanyoru
"""
请先安装 pyexecjs node.js
pipx install pyexecjs
get node.js by https://nodejs.org/zh-cn
or get node by docker:
docker pull node:22-alpine
"""

os.environ['EXECJS_RUNTIME'] = 'Node'

JS_PATH = Path(__file__).parent

def js_from_file(file_name):
    """
    读取js文件
    :return:
    """
    with open(file_name, 'r', encoding='UTF-8') as file:
        result = file.read()
    return result


ctx = execjs.compile(js_from_file(JS_PATH/"commonjs"/"index.js"), cwd=JS_PATH/"commonjs")


def get_random_name(num: int = 1, sex: int = 0):
    return ctx.call("getName", num)


def get_random_sect_name(num):
    return ctx.call("getClan", num)

