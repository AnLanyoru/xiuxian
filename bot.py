

import nonebot
from loguru import logger
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.log import default_format

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

logger.add("error.log", level="ERROR", format=default_format, rotation="1 week")

nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()