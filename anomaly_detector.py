import time

import utils.config_loader as config_loader
from models.models_set import ModelsSet
import data_processing.detector as detector
import data_processing.history as history
import data_getter
import utils.normalizer as normalizer
import views


def run(config_file: str, endep: int, 
        item_names: list[str] = [], 
        host_names: list[str] = [], 
        group_names: list[str] = [],
        show_view: bool = True
        ) -> tuple[dict, dict, dict]:
    config_loader.load_config(config_file)
    conf = config_loader.conf
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
    lambda1_threshold = conf.get('lambda1_threshold', 3.0)
    lambda2_threshold = conf.get('lambda2_threshold', 1.0)
    lambda3_threshold = conf.get('lambda3_threshold', 2.0)
    kconf = conf.get("kmeans", {})
    k = kconf.get("k", 10)
    threshold = kconf.get("threshold", 0.1)
    max_iterations = kconf.get("max_iterations", 10)
    n_rounds = kconf.get("n_rounds", 10)

    # data processing
    clusters = {}
    for data_source in data_sources:
        data_source_name = data_source["name"]
        ms = ModelsSet(data_source_name)
        dg = data_getter.get_data_getter(data_source)
        itemIds = dg.get_itemIds(item_names=item_names, host_names=host_names, group_names=group_names)
        diff_startep = 0

        oldendep = ms.history_updates.get_endep()
        if oldendep > 0:
            if h_startep1 > oldendep:
                ms.history.truncate()
                diff_startep = h_startep1
            else:
                diff_startep = oldendep + 1
        else:
            diff_startep = h_startep1
        
        # get base clocks
        base_clocks = normalizer.get_base_clocks(diff_startep, endep, history_interval)
        # update history
        history.update_history(data_source, itemIds, base_clocks, h_startep1)

        # detect anomaly
        clusters_info = detector.detect(data_source, 
           t_startep, h_startep2, endep,
           lambda1_threshold, lambda2_threshold, lambda3_threshold,
           itemIds, group_names, 
           k, threshold, max_iterations, n_rounds)
        clusters[data_source_name] = clusters_info

        # update history updates
        ms.history_updates.upsert_updates(h_startep1, endep)

    # view
    if show_view:
        for view_source in conf.get('view_sources', []):
            v = views.get_view(view_source)
            v.show(clusters[view_source['name']])

    return clusters


if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('--start', type=int, help='Start epoch. Data will be initialized if start is given.')
    parser.add_argument('--end', type=int, help='End epoch.')
    parser.add_argument('--itemIds', type=int, nargs='+', help='itemIds')
    parser.add_argument('--output', type=str, help='output file')
    parser.add_argument('--no-view', dest='view', action='store_false', help='do not show view')

    args = parser.parse_args()
    config_file = args.config
    startep = args.start
    endep = args.end
    itemIds = args.itemIds
    output = args.output

    clusters = run(config_file, endep, itemIds, show_view=args.view)

    # pretty print json clusters
    import json
    with open(output, 'w') as f:
        json.dump(clusters, f, indent=4)

    