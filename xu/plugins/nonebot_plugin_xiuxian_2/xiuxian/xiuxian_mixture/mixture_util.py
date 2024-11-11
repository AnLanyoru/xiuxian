from mixture_database import MixtureData


# 初始化合成表对象
class MixtureTable:
    def __init__(self):
        self.item_id = None
        self.need_items_id = []
        self.need_items_num = []
        self.state = []
        self.is_bind_mixture = 0
        pass


class Mixture:
    def __init__(self):
        self.all_table = {}

    def get_all_table_cls(self) -> dict | None:
        tables = MixtureData().get_all_table()
        if tables:
            for table_id in range(len(tables)):
                table = tables[table_id]
                cls = MixtureTable()
                self.all_table[table_id] = cls
                self.all_table[table_id].item_id = table['item_id']
                self.all_table[table_id].need_items_id = table['need_items_id']
                self.all_table[table_id].need_items_num = table['need_items_num']
                self.all_table[table_id].state = table['state']
                self.all_table[table_id].is_bind_mixture = table['is_bind_mixture']
            return self.all_table
        else:
            return None
        pass
