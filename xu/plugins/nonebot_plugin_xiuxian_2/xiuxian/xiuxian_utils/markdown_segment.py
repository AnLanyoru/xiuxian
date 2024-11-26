"""OneBot v11 消息类型 markdown扩充。

FrontMatter:
    sidebar_position: 5
    description: onebot.v11.message 模块
"""

from typing_extensions import Self
from nonebot.adapters.onebot.v11 import MessageSegment


class MessageSegmentPlus(MessageSegment):
    @classmethod
    def markdown_template(
            cls,
            md_id: str,
            msg_body: list,
    ) -> Self:
        """
        markdown模板
        :param md_id: 模板id
        :param msg_body: 模板参数
        :return:
        """
        return cls(
            "markdown",
            {
                "data": {
                    "markdown": {
                        "custom_template_id": md_id,
                        "params": msg_body
                    }
                }
            }
        )

    @classmethod
    def markdown(
            cls,
            msg_body: list,
    ) -> Self:
        """
        原生markdown
        :param msg_body: 消息内容
        :return:
        """
        return cls(
            "markdown",
            {
                "data": {
                    "markdown": {
                        "content": msg_body
                    }
                }
            }
        )
