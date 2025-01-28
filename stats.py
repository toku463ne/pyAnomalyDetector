from typing import List
import time

import utils.config_loader as config_loader
import data_processing.trends_stats as trends_stats
from models.models_set import ModelsSet




def update_stats(config_file: str, 
                endep: int, diff_startep: int =0, 
                item_names: List[str] = None, 
                host_names: List[str] = None, 
                group_names: List[str] = None,
                itemIds: List[int] = None,
                initialize: bool = False, max_itemIds = 0):
    config_loader.load_config(config_file)
    conf = config_loader.conf
    
    if item_names is None:
        item_names = conf.get('item_names', [])
    if host_names is None:
        host_names = conf.get('host_names', [])
    if group_names is None:
        group_names = conf.get('group_names', [])
    if itemIds is None:
        itemIds = conf.get('itemIds', [])
    data_sources = conf['data_sources']

    if endep == 0:
        endep = int(time.time())
    
    # don't include the very last epoch
    endep -= 1

    # update stats
    for data_source in data_sources:
        oldstartep: int = 0
        startep: int = 0
        diff_startep: int = 0
        ms = ModelsSet(data_source["name"])

        if initialize:
            ms.trends_updates.truncate()
    
        if diff_startep == 0:
            diff_startep = ms.trends_updates.get_endep()

        oldstartep = ms.trends_updates.get_startep()

        # get old epoch from trends_interval and trends_retention
        trends_interval = conf['trends_interval']
        trends_retention = conf['trends_retention']
        startep = endep - trends_interval * trends_retention
        if diff_startep == 0:
            diff_startep = startep
        trends_stats.update_trends_stats(data_source, startep, diff_startep, endep, 
                                         oldstartep, 
                                         item_names=item_names, host_names=host_names, group_names=group_names,
                                         itemIds=itemIds,
                                         initialize=initialize, max_itemIds=max_itemIds)

        ms.trends_updates.upsert_updates(startep, endep)


if __name__ == "__main__":
    #import os
    #os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
    #update_stats("tests/test_zabbix.d/config.yml", 0, initialize=True)

    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    #parser.add_argument('--end', type=int, help='End epoch.')
    parser.add_argument('--init', action='store_true', help='If clear DB first')
    args = parser.parse_args()

    update_stats(args.config, 0, initialize=args.init)