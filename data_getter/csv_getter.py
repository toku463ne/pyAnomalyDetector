"""
class to get data from CSV files
"""
import os, json, csv

from data_getter.data_getter import DataGetter
from typing import Dict, List
import pandas as pd # type: ignore

class CsvGetter(DataGetter):
    fields = ['itemid', 'clock', 'value']
    trends_filename = 'trends.csv.gz'
    history_filename = 'history.csv.gz'
    items_filename = 'items.csv.gz' # group_name, hostid, itemid
    
    def init_data_source(self, data_source_config):
        self.data_dir = data_source_config['data_dir']
        

    def check_conn(self) -> bool:
        # check if the data_dir exists
        return os.path.exists(self.data_dir)
    
    def get_history_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        df = pd.read_csv(os.path.join(self.data_dir, self.history_filename))
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields)
        df.columns = self.fields

        # filter by time
        df = df[(df['clock'] >= startep) & (df['clock'] <= endep)]

        # filter by itemIds
        if len(itemIds) > 0:
            df = df[df['itemid'].isin(itemIds)]
        return df
    
    def get_trends_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        df = pd.read_csv(os.path.join(self.data_dir, self.trends_filename))
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields)
        df.columns = self.fields

        # filter by time
        df = df[(df['clock'] >= startep) & (df['clock'] <= endep)]

        # filter by itemIds
        if len(itemIds) > 0:
            df = df[df['itemid'].isin(itemIds)]
        return df
    
    def get_itemIds(self, item_names: List[str] = [], 
                    host_names: List[str] = [], 
                    group_names: List[str] = [],
                    max_itemIds = 0,
                    itemIds: List[int] = []) -> List[int]:
        df = pd.read_csv(os.path.join(self.data_dir, self.history_filename))
        results = df['itemid'].unique().tolist()
        # filter by itemIds
        if len(itemIds) > 0 and len(results) > 0:
            results = [itemid for itemid in results if itemid in itemIds]
        
        if max_itemIds > 0:
            results = results[:max_itemIds]
        return results


    def classify_by_groups(self, itemIds: List[int], group_names: List[str]) -> Dict[str, List[int]]:
        items = {}
        with open(os.path.join(self.data_dir, self.items_filename), 'r') as f:
            csvreader = csv.DictReader(f)
            for row in csvreader:
                if row['itemid'] not in itemIds:
                    continue
                items[row['itemid']] = {
                    'group_name': row['group_name'],
                    'hostid': row['hostid']
                }

        groups = {}
        for group_name in group_names:
            groups[group_name] = [int(itemid) for itemid, item in items.items() if item['group_name'] == group_name]

        return groups
    
    
    def get_item_host_dict(self, itemIds: List[int]) -> Dict[int, str]:
        items = {}
        with open(os.path.join(self.data_dir, self.items_filename), 'r') as f:
            csvreader = csv.DictReader(f)
            for row in csvreader:
                if row['itemid'] not in itemIds:
                    continue
                items[row['itemid']] = row['hostid']
        return items