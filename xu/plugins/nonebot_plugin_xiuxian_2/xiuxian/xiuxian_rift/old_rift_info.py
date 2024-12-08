import pickle
from pathlib import Path
import os
import datetime
from .riftmake import Rift


class OLD_RIFT_INFO(object):
    def __init__(self):
        self.dir_path = Path(__file__).parent
        self.data_path = os.path.join(self.dir_path, "rift_info.plk")
        try:
            with open(self.data_path, 'rb') as f:
                self.data = pickle.load(f)
        except:
            self.info = {}
            with open(self.data_path, mode="wb") as f:
                pickle.dump(self.info, f)
            with open(self.data_path, mode="rb") as f:
                self.data = pickle.load(f)

    def __save(self):
        """
        :return:保存
        """
        with open(self.data_path, 'wb') as f:
            pickle.dump(self.data, f)

    def __save_none(self):
        """
        :return:保存
        """
        with open(self.data_path, 'wb') as f:
            pickle.dump({}, f)

    def save_rift(self, group_rift):
        """
        保存rift
        :param group_rift:
        """
        self.data = group_rift
        self.__save()
        return True

    def read_rift_info(self):
        """
        读取rift信息
        """
        world_rift = self.data
        self.__save_none()
        return world_rift


old_rift_info = OLD_RIFT_INFO()

