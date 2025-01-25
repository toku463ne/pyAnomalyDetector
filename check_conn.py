import time
from typing import List, Dict, Tuple

import utils.config_loader as config_loader
from models.models_set import ModelsSet
import data_processing.detector as detector
import data_processing.history as history
import data_getter
import utils.normalizer as normalizer
import views


def run_check(config_file: str) -> bool:
    config_loader.load_config(config_file)
    conf = config_loader.conf
    data_sources = conf['data_sources']

    try:
        for data_source in data_sources:
            data_source_name = data_source["name"]
            ms = ModelsSet(data_source_name)
            if ms.check_conn() == False:
                return False

        for data_source in data_sources:
            data_source_name = data_source["name"]
            dg = data_getter.get_data_getter(data_source)
            if dg.check_conn() == False:
                return False
            
        for view_source in conf.get('view_sources', []):
            v = views.get_view(view_source)
            if v.check_conn() == False:
                return False
    except Exception as e:
        print(e)
        return False
    return True

if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')

    args = parser.parse_args()

    run_check(config_file)

    
    