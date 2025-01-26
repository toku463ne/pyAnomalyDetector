from typing import List, Dict
import csv

import __init__
import utils.config_loader as config_loader
from data_getter.zabbix_getter import ZabbixGetter

def trends2csv(data_source_config: Dict, itemIds: List[int], startep: int, endep: int, outfile: str):
    z = ZabbixGetter(data_source_config)
    df = z.get_trends_data(startep, endep, itemIds=itemIds)
    # Save the DataFrame to a gzipped CSV file
    df.to_csv(outfile, index=False, compression='gzip')


def history2csv(data_source_config: Dict, itemIds: List[int], startep: int, endep: int, outfile: str):
    z = ZabbixGetter(data_source_config)
    df = z.get_history_data(startep, endep, itemIds=itemIds)
    # Save the DataFrame to a gzipped CSV file
    df.to_csv(outfile, index=False, compression='gzip')


def ouput_item_relations(data_source_config: Dict, itemIds: List[int], group_names: List[str], outfile: str):
    z = ZabbixGetter(data_source_config)
    df = z.get_item_relations(itemIds, group_names)
    # Save the DataFrame to a gzipped CSV file
    df.to_csv(outfile, index=False, compression='gzip')
    


if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('--end', type=int, default=0, help='End epoch.')
    parser.add_argument('--itemsfile', type=str, help='txt file including itemids')
    parser.add_argument('--groupsfile', type=str, help='txt file including host group names')
    parser.add_argument('--outdir', type=str, help='output directory')
    args = parser.parse_args()
    
    itemIds = []
    with open(args.itemsfile, "r") as f:
        for itemId in f:
            itemIds.append(itemId)

    group_names = []
    with open(args.groupsfile, "r") as f:
        for g in f:
            group_names.append(g.strip())

    config_loader.load_config(args.config)
    conf = config_loader.conf
    endep = args.end

    trends_interval = conf["trends_interval"]
    trends_retention = conf["trends_retention"]
    trend_startep = endep - trends_interval * trends_retention

    history_interval = conf["history_interval"]
    history_retention = conf["history_retention"]
    history_startep = endep - history_interval * history_retention
    
    trends_file = os.path.join(args.outdir, "trends.csv.gz")
    history_file = os.path.join(args.outdir, "history.csv.gz")
    groups_file = os.path.join(args.outdir, "groups.csv.gz")
    
    data_source_config = {}
    for data_source_config in conf["data_sources"]:
        if data_source_config["type"] == "zabbix":
            break
    if data_source_config == {}:
        print("no data source with type=zabbix")
        exit(1)


    trends2csv(data_source_config, itemIds, trend_startep, endep, trends_file)
    history2csv(data_source_config, itemIds, history_startep, endep, history_file)
    ouput_item_relations(data_source_config, itemIds, group_names, groups_file)

