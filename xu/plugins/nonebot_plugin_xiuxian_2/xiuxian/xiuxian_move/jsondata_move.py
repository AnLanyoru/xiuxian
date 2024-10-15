try:
    import ujson as json
except ImportError:
    import json
import os
from pathlib import Path
from nonebot.log import logger

PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


class Move:
    def __init__(self):
        self.start_id = 0
        self.to_id = 0
        self.need_time = 0


def read_move_data(user_id):
    user_id = str(user_id)
    FILEPATH = PLAYERSDATA / user_id / "moveinfo.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def save_move_data(user_id, data):
    user_id = str(user_id)
    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info("目录不存在，创建目录")
        os.makedirs(PLAYERSDATA / user_id)
    FILEPATH = PLAYERSDATA / user_id / "moveinfo.json"
    data = json.dumps(data, ensure_ascii=False, indent=3)
    save_mode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True
