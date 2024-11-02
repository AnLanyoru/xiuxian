import sqlite3
from datetime import datetime
from pathlib import Path
import threading

DATABASE = Path()
xiuxian_num = "578043031"  # 这里其实是修仙1作者的QQ号
impart_number = "123451234"
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


class MixtureData:
    global xiuxian_num
    _instance = {}
    _has_init = {}

    # 单例化数据库连接
    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(MixtureData, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "mixture.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            else:
                self.database_path /= "mixture.db"
                self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self.lock = threading.Lock()
            print(f"合成表数据库已连接！")
            self.sql_mixture = ["item_id", "need_items_id", "need_items_num", "create_time",
                                "update_time", "state", "is_bind_mixture"]
            self._check_data()

    def close(self):
        self.conn.close()
        print(f"合成表数据库关闭！")

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()
        try:
            c.execute(f"select count(1) from mixture_table")
        except sqlite3.OperationalError:
            c.execute("""CREATE TABLE "mixture_table" (
      "item_id" INTEGER NOT NULL,
      "need_items_id" TEXT DEFAULT NULL,
      "need_items_num" TEXT DEFAULT NULL,
      "create_time" TEXT,
      "update_time" TEXT,
      "state" TEXT,
      "is_bind_mixture" integer DEFAULT 0
      );""")

        for i in self.sql_mixture:  # 自动补全
            try:
                c.execute(f"select {i} from mixture_table")
            except sqlite3.OperationalError:
                print("<yellow>mixture_table有字段不存在，开始创建\n</yellow>")
                sql = f"ALTER TABLE user_xiuxian ADD COLUMN {i} INTEGER DEFAULT 0;"
                print(f"<green>{sql}</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        MixtureData().close()

    # 上面是数据库校验，别动

    def get_all_table(self) -> list | None:
        """
        获取所有合成表数据，字典输出
        :return:
        """
        sql = f"SELECT * FROM mixture_table"
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        results = []
        for row in result:
            back_dict = dict(zip(columns, row))
            results.append(back_dict)
        return results

    def get_table_by_item_id(self, item_id):
        """
        获取物品合成表
        :param item_id: 合成物品id
        :return:
        """
        sql = f"select * from mixture_table WHERE item_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (item_id,))
        result = cur.fetchone()
        if not result:
            return None

        columns = [column[0] for column in cur.description]
        item_dict = dict(zip(columns, result))
        return item_dict
        pass

    def send_table(self, item_id: int, need_items_id: list, need_items_num: list,
                   state='', is_bind_mixture=0):
        """
        插入配方至合成表
        :param item_id: 合成物品ID
        :param need_items_id: 需求物品id
        :param need_items_num: 需求物品数量
        :param state: 特殊状态传导
        :param is_bind_mixture: 是否合成为绑定物品,0-非绑定,1-绑定
        :return: None
        """
        need_items_id = str(need_items_id)
        need_items_num = str(need_items_num)
        now_time = datetime.now()
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        table = self.get_table_by_item_id(item_id)
        if table:
            # 判断是否存在，存在则更新维护日期
            sql = f"""INSERT INTO mixture_table (item_id, need_items_id, need_items_num, update_time, state, is_bind_mixture)
                VALUES (?,?,?,?,?,?)"""
            cur.execute(sql, (item_id, need_items_id, need_items_num, now_time, state, is_bind_mixture))
        else:
            # 判断是否存在，不存在则INSERT
            sql = f"""INSERT INTO mixture_table (item_id, need_items_id, need_items_num, create_time, update_time, state, is_bind_mixture)
                VALUES (?,?,?,?,?,?,?)"""
            cur.execute(sql, (item_id, need_items_id, need_items_num, now_time, now_time, state, is_bind_mixture))
        self.conn.commit()
        return True


def fast_create():
    print("欢迎~~")
    print("当前已有合成表：\n", MixtureData().get_all_table())
    act = int(input("请决定您要进行的操作：\n1.创建合成表\n2.删除合成表\n"))
    if act == 1:
        item_id = int(input("合成目标物品id："))

        item_num = int(input("合成所需物品种类："))
        need_items_id = []
        need_items_num = []
        for n in range(item_num):
            need_item_id = int(input(f"请输入第{n + 1}个材料物品id:"))
            need_items_id.append(need_item_id)
            need_item_num = int(input(f"请输入第{n + 1}个材料物品所需数量:"))
            need_items_num.append(need_item_num)
        get_bind_num = {'y': 1, 'n': 0}
        is_bind_mixture = get_bind_num[str(input(f"是否绑定(y/n):"))]
        state = str(input(f"特殊赋值（可不填）:"))
        if state:
            pass
        else:
            state = ''
        is_pass = MixtureData().send_table(item_id, need_items_id, need_items_num, state, is_bind_mixture)
        if is_pass:
            print("创建新合成表成功，当前总合成表：", MixtureData().get_all_table())
        else:
            print("创建合成表遇到未知问题，请联系安兰！")
        pass
    else:
        print("暂未开放")
    MixtureData().close()
    input("按任意键退出")


if __name__ == '__main__':
    fast_create()
