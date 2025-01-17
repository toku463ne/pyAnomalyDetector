"""
Super class to get data from different sources
"""

from abc import abstractmethod
import pandas as pd # type: ignore



class DataGetter:
    def __init__(self, data_source_config):
        self.init_data_source(data_source_config)


    # function to initialize the data source. 
    @abstractmethod
    def init_data_source(self, data_source_config):
        pass

    # function to get data from the data source. 
    # Returns pandas dataframe with columns: itemid, clock, value
    @abstractmethod
    def get_history_data(self, startep: int, endep: int, itemIds: list[int] = []) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_trends_data(self, startep: int, endep: int, itemIds: list[int] = []) -> pd.DataFrame:
        pass

    # function to get itemIds from the data source. 
    @abstractmethod
    def get_itemIds(self, item_names: list[str] = [], 
                    host_names: list[str] = [], 
                    group_names: list[str] = []) -> list[int]:
        pass

    # function to get dict of itemId to hostId from the data source.
    @abstractmethod
    def get_item_host_dict(self, itemIds: list[int]=[]) -> dict[int, int]:
        pass

    
    # funtion to classify items by host groups
    def classify_by_groups(self, itemIds: list[int], group_names: list[str]) -> dict:
        pass
        