"""
class to get metrics from URL
Expected structure in the URL:
    base_url/
    |- host1/history.csv
    |- host2/history.csv
    |- host3/history.csv
Define host_names and group_names structure in the config file (yaml)
example:
    group_names:
        - group1
            host_names:
                - host1
                - host2
        - group2
            host_names:
                - host3
                - host4
"""
from data_getter.data_getter import DataGetter
from typing import Dict, List

import requests
import json
import pandas as pd

class LoganGetter(DataGetter):
    fields = ['itemid', 'clock', 'value']
    loggroups_fields = ['itemid', 'count', 'score', 'text']

    def init_data_source(self, data_source_config):
        self.base_url = data_source_config['base_url']
        self.group_names = data_source_config['group_names']
        self.host_names = []
        for node in self.group_names:
            self.host_names.extend(node['host_names'])
        self.data: Dict[str, pd.DataFrame] = {}
        self.loggroup_data: Dict[str, pd.DataFrame] = {}
        self.data_loaded = False
        self.trends_interval = data_source_config['trends_interval']
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def check_conn(self) -> bool:
        try:
            response = requests.get(self.base_url, headers=self.headers)
            if response.status_code == 200:
                return True
        except Exception as e:
            print(e)
        return False
    

    def _load_host_data(self, host_name: str):
        # get loggroups data
        url = self.base_url + host_name + '/logGroups.csv'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = pd.read_csv(url)
            data.columns = self.loggroups_fields
        else:
            data = pd.DataFrame(columns=self.loggroups_fields)
        self.loggroup_data[host_name] = data
        
        # get metrics data
        url = self.base_url + host_name + '/history.csv'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = pd.read_csv(url)
            data.columns = self.fields
        else:
            data = pd.DataFrame(columns=self.fields)
        self.data[host_name] = data


    def _load_data(self, force: bool = False):
        if not force and self.data_loaded:
            return

        self.data = {}
        for host in self.host_names:
            self._load_host_data(host)
        self.data_loaded = True
    

    def get_itemIds(self, item_names: List[str] = [],
                    host_names: List[str] = [], 
                    group_names: List[str] = []) -> List[int]:
        if len(self.data) == 0:
            self._load_data()
        itemIds = []
        # filter by host_names
        host_names = host_names if len(host_names) > 0 else self.host_names
        # filter host_names by group_names
        if len(group_names) > 0:
            host_names = [host for host in host_names if host in group_names]
        
        if len(item_names) > 0:
            # filter loggroups_data['text'] by item_names regex
            for host in host_names:
                data = self.loggroup_data[host]
                itemIds.extend(data[data['text'].str.contains('|'.join(item_names))]['itemid'].tolist())
        else:
            for host in host_names:
                data = self.data[host]
                itemIds.extend(data['itemid'].tolist())

        return itemIds
    

    def get_history_data(self, startep, endep, itemIds = ...):
        if len(self.data) == 0:
            self._load_data()
        data = pd.DataFrame(columns=self.fields)
        for host in self.host_names:
            data = pd.concat([data, self.data[host]])
            # filter by itemIds
            if itemIds is not ...:
                data = data[data['itemid'].isin(itemIds)]
            # filter by time
            data = data[(data['clock'] >= startep) & (data['clock'] <= endep)]
        return data
            
    def get_trends_data(self, startep, endep, itemIds = ...):
        data = self.get_history_data(startep, endep, itemIds)
        # sum values by trends_interval, use the first clock
        data['clock'] = data['clock'] // self.trends_interval
        data = data.groupby(['itemid', 'clock']).mean().reset_index()
        return data
    
    def get_trends_full_data(self, startep, endep, itemIds = ...):
        data = self.get_history_data(startep, endep, itemIds)
        # sum values by trends_interval, use the first clock
        data['clock'] = data['clock'] // self.trends_interval
        data = data.groupby(['itemid', 'clock']).agg({'value': ['min', 'mean', 'max']}).reset_index()
        return data
    
    def get_item_host_dict(self, itemIds = ...):
        if len(self.data) == 0:
            self._load_data()
        item_host_dict = {}
        for host in self.host_names:
            data = self.data[host]
            if itemIds is not ...:
                data = data[data['itemid'].isin(itemIds)]
            item_host_dict.update(data.set_index('itemid')['hostid'].to_dict())
        return item_host_dict
    
    def classify_by_groups(self, itemIds: List[int], group_names: List[str]) -> dict:
        if len(self.data) == 0:
            self._load_data()
        groups = {}
        for group in group_names:
            groups[group] = []
            for host in self.host_names:
                if host in group_names:
                    data = self.loggroup_data[host]
                    groups[group].extend(data[data['itemid'].isin(itemIds)]['text'].tolist())
        return groups



    