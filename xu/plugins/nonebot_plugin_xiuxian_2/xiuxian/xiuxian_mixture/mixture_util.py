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
