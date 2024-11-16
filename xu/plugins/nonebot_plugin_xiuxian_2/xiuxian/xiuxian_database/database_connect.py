import psycopg2
from nonebot import logger
from database_config import database_config  # 这是上面的config()代码块，已经保存在config.py文件中


class DataBase:
    def __init__(self):
        params = database_config()
        logger.opt(colors=True).success(f"<green>尝试登录到数据库</green>")
        self.conn = psycopg2.connect(
            database=params['database'],
            user=params['user'],
            password=params['password'],
            host=params['host'],
            port=params['post'])
        self.cur = self.conn.cursor()
        self.cur.execute('SELECT version()')
        db_version = self.cur.fetchone()
        logger.opt(colors=True).success(f"<green>登录数据库成功，数据库版本：{db_version}</green>")

    def close_db(self):
        self.cur.close()
        self.conn.close()


database = DataBase()

