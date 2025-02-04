import time
from typing import List, Dict, Tuple
import json

import utils.config_loader as config_loader
from models.models_set import ModelsSet
import views


def prepare(config_file: str) :
    config_loader.load_config(config_file)
    conf = config_loader.conf

    for view_source in conf.get('view_sources', []):
        ms = ModelsSet(view_source["data_source_name"])
        df = ms.anomalies.get_data()
        v = views.get_view(view_source)
        if v is not None:
            v.show(df)



if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')

    args = parser.parse_args()
    config_file = args.config

    clusters = prepare(config_file)

    