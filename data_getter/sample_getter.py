"""
class to get sample data
subclass of DataGetter
"""
import os
import pandas as pd # type: ignore
import yaml

from data_getter.data_getter import DataGetter
from utils.data_generator import *

class SampleGetter(DataGetter):
    def init_data_source(self, data_source):
        self.seed = data_source.get('seed', 0)
        config_file = os.path.join(os.path.dirname(__file__), 'sample_getter.d', data_source['sample_config'])
        with open(config_file) as f:
            self.samples = yaml.safe_load(f)
            
        

    def _get_single_data(self, startep: int, endep: int, properties: dict) -> list[float]:
        values: list[float] = None
        data_type: str = properties['type']
        unitsecs: int = properties.get('unitsecs', 300)
        num_samples: int = (endep - startep) // unitsecs
        # get the values from utils.data_generator
        if data_type == 'sine_wave':
            values = sine_wave(num_samples, **properties)
        elif data_type == 'exponential_wave':
            values = exponential_wave(num_samples, **properties)
        elif data_type == 'logarithmic_wave':
            values = logarithmic_wave(num_samples, **properties)
        elif data_type == 'normal_distribution_wave':
            values = normal_distribution_wave(num_samples, **properties)
        elif data_type == 'step_function_values':
            values = step_function_values(num_samples, **properties)
        elif data_type == 'stairs_wave':
            values = stairs_wave(num_samples, **properties)
        elif data_type == 'oneweek_normal_distribution_wave':
            values = oneweek_normal_distribution_wave(num_samples, **properties)
        elif data_type == 'convex_wave':
            values = convex_wave(num_samples, **properties)
        elif data_type == 'generate_monotonic_values':
            values = generate_monotonic_values(num_samples, **properties)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        return values


    def _get_data(self, startep: int, endep: int, itemIds: list[int] = [], use_history: bool = True) -> pd.DataFrame: 
        data = pd.DataFrame(columns=['itemid', 'clock', 'value'])
        for sample in self.samples:
            itemid = sample['itemid']
            if itemIds and itemid not in itemIds:
                continue
            if use_history:
                properties = sample['history']
            else:
                properties = sample['trend']

            values = self._get_single_data(startep, endep, properties)
            for i in range(len(values)):
                new_data = pd.DataFrame([{'itemid': sample['itemid'], 'clock': startep+i, 'value': values[i]}])
                new_data = new_data.dropna(how='all')
                if not new_data.empty:
                    data = pd.concat([data, new_data], ignore_index=True)
        return data

    def get_history_data(self, startep: int, endep: int, itemIds: list[int] = []) -> pd.DataFrame: 
        return self._get_data(startep, endep, use_history=True, itemIds=itemIds)
    
    def get_trends_data(self, startep: int, endep: int, itemIds: list[int] = []) -> pd.DataFrame:
        return self._get_data(startep, endep, use_history=False, itemIds=itemIds)
        
    def get_itemIds(self, item_names: list[str], host_names: list[str], group_names: list[str]) -> list[int]:
        return [sample['itemid'] for sample in self.samples]
    
    def get_item_host_dict(self, itemIds = ...) -> dict[int, int]:
        return {sample['itemid']: sample['hostid'] for sample in self.samples if itemIds and sample['itemid'] in itemIds}
        
    def classify_itemIds(self, itemIds: list[int], host_groups: list[str]) -> dict[str, list[int]]:
        return {"all": itemIds}