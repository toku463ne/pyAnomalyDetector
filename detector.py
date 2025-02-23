import time
from typing import List, Dict, Tuple

import utils.config_loader as config_loader
from models.models_set import ModelsSet
import data_processing.detector as detector
from data_processing.history_stats import HistoryStats
import data_getter
import utils.normalizer as normalizer


def run(config_file: str, endep: int = 0, 
        item_names: List[str] = None, 
        host_names: List[str] = None, 
        group_names: List[str] = None,
        itemIds: List[int] = None,
        max_itemIds = 0,
        initialize = False,
        skip_history_update = False,
        trace_mode = False
        ) -> Tuple[Dict, Dict, Dict]:
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
    
    history_interval = conf.get('history_interval', 600)
    trend_interval = conf.get('trend_interval', 3600*3)
    history_retention = conf.get('history_retention', 18)
    trend_retention = conf.get('trend_retention', 8*14)
    history_recent_retention = conf.get('history_recent_retention', 6)
    h_startep1 = endep - history_retention * history_interval
    h_startep2 = endep - history_recent_retention * history_interval
    t_startep = endep - trend_retention * trend_interval

    # data processing
    clusters = {}
    for data_source in data_sources:
        data_source_name = data_source["name"]
        ms = ModelsSet(data_source_name)
        dg = data_getter.get_data_getter(data_source)

        oldstartep = ms.history_updates.get_startep()

        if initialize:
            ms.history.truncate()
            ms.history_stats.truncate()
            ms.anomalies.truncate()
            ms.history_updates.truncate()

        itemIds = dg.get_itemIds(item_names=item_names, 
                                 host_names=host_names, 
                                 group_names=group_names,
                                 itemIds=itemIds,
                                 max_itemIds=max_itemIds)
        # only itemIds existing in trends_stats table
        itemIds, _ = ms.trends_stats.separate_existing_itemIds(itemIds)
        diff_startep = 0

        oldendep = ms.history_updates.get_endep()
        if oldendep > 0:
            if h_startep1 > oldendep:
                ms.history_updates.truncate()
                diff_startep = h_startep1
            else:
                diff_startep = oldendep + 1
        else:
            diff_startep = h_startep1
        
        hs = HistoryStats(data_source=data_source, 
                          item_names=item_names, 
                          host_names=host_names, 
                          group_names=group_names, 
                          itemIds=itemIds, 
                          max_itemIds=max_itemIds)
        if skip_history_update == False:
            #ms.history.truncate()
            hs.update_stats(h_startep1, diff_startep, endep, oldstartep)

            # update history
            #if len(existing) > 0:
            #    #base_clocks_diff = normalizer.get_base_clocks(diff_startep, endep, history_interval)
            #    #history.update_history(data_source, existing, base_clocks_diff, h_startep1)
            #    history.update_history(data_source, existing, diff_startep, endep)
            #if len(nonexisting) > 0:
            #    #base_clocks_full = normalizer.get_base_clocks(h_startep1, endep, history_interval)
            #    #history.update_history(data_source, nonexisting, base_clocks_full, h_startep1)
            #    history.update_history(data_source, nonexisting, h_startep1, endep)

        base_clocks = normalizer.get_base_clocks(h_startep1, endep-1, history_interval)


        # detect anomaly
        data = detector.detect(data_source, 
           t_startep, h_startep1, h_startep2, endep,
           base_clocks,
           itemIds, group_names, 
           skip_history_update,
           trace_mode=trace_mode)
        clusters[data_source_name] = data

        # update history updates
        if skip_history_update == False:
            ms.history_updates.upsert_updates(h_startep1, endep)

    return clusters


if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('--end', type=int, default=0, help='End epoch.')
    parser.add_argument('--items', type=int, nargs='+', help='item names')
    parser.add_argument('--hosts', type=int, nargs='+', help='host names')
    parser.add_argument('--groups', type=int, nargs='+', help='host group names')
    parser.add_argument('--output', type=str, help='output file', default="")
    parser.add_argument('--init', action='store_true', help='If clear DB first')
    parser.add_argument('--skip-history-update', action='store_true', help='skip to update local history')
    

    args = parser.parse_args()
    config_file = args.config
    endep = args.end
    items = args.items
    hosts = args.hosts
    groups = args.groups
    output = args.output

    clusters = run(config_file, endep, items, hosts, groups, initialize=args.init, skip_history_update=args.skip_history_update)

    # pretty print json clusters
    import json
    if output != "":
        for data_source_name, df in clusters.items():
            if df:
                df.to_csv(f"{output}_{data_source_name}.csv", index=False)
    else:
        for data_source_name, df in clusters.items():
            print(data_source_name)
            print(df)

    