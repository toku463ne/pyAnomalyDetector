import time
from typing import List, Dict, Tuple
import json

import utils.config_loader as config_loader
import views


def prepare(config_file: str, data_file: str) :
    data = {}
    with open(data_file, "r") as f:
        data = json.load(f)    

    config_loader.load_config(config_file)
    conf = config_loader.conf

    for view_source_name, view_source in conf.get('view_sources', []).items():
        view_source['name'] = view_source_name
        v = views.get_view(view_source)
        v.show(data[view_source_name])



if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('-d', '--data', type=str, help='output of anomaly detection')

    args = parser.parse_args()
    config_file = args.config
    data_file = args.data

    clusters = prepare(config_file, data_file)

    