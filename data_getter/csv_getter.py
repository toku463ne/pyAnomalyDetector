"""
class to get data from CSV files
"""
import os, json, csv, gzip

from data_getter.data_getter import DataGetter
from typing import Dict, List
import pandas as pd # type: ignore

class CsvGetter(DataGetter):
    fields = ['itemid', 'clock', 'value']
    fields_full = ['itemid', 'clock', 'value_min', 'value_avg', 'value_max']
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

        # sort by itemid, clock
        df = df.sort_values(['itemid', 'clock'])
        return df
    
    def get_trends_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        df = self.get_trends_full_data(startep, endep, itemIds)
        # convert value_avg to value
        df['value'] = df['value_avg']
        # sort by itemid, clock
        df = df.sort_values(['itemid', 'clock'])
        return df[self.fields]
    
    
    def get_trends_full_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        df = pd.read_csv(os.path.join(self.data_dir, self.trends_filename))
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields_full)
        df.columns = self.fields_full

        # filter by time
        df = df[(df['clock'] >= startep) & (df['clock'] <= endep)]

        # filter by itemIds
        if len(itemIds) > 0:
            df = df[df['itemid'].isin(itemIds)]

        # sort by itemid, clock
        df = df.sort_values(['itemid', 'clock'])
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
        with gzip.open(os.path.join(self.data_dir, self.items_filename), 'rt') as f:
            csvreader = csv.DictReader(f)
            for row in csvreader:
                if int(row['itemid']) not in itemIds:
                    continue
                items[row['itemid']] = {
                    'group_name': row['group_name'],
                    'hostid': row['hostid']
                }

        groups = {}
        for group_name in group_names:
            groups[group_name] = [int(itemid) for itemid, item in items.items() if item['group_name'] == group_name]

        return groups
    
    
    def get_item_details(self, itemIds: List[int]) -> Dict:
        items = {}
        # open items.csv.gz
        with gzip.open(os.path.join(self.data_dir, self.items_filename), 'rt') as f:
            csvreader = csv.DictReader(f)
            for row in csvreader:
                itemId = int(row['itemid'])
                if itemId not in itemIds:
                    continue
                items[itemId] = {
                    "hostid": int(row['hostid']),
                    "host_name": row.get('host_name', ''),
                    "item_name": row.get('item_name', '')
                }
        return items