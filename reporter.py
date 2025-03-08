from typing import Dict

from models.models_set import ModelsSet
import utils.config_loader as config_loader
import data_getter

def report(config_file: str, epoch: int) -> Dict:
    config_loader.load_config(config_file)
    conf = config_loader.conf

    anomaly_cache_ep = epoch - conf['anomaly_cache_period']
    data = {}
    for data_source in conf["data_sources"]:
        ms = ModelsSet(data_source["name"])
        # get anomaly dataframe
        df = ms.anomalies.get_data([f"created >= {anomaly_cache_ep}",
                                    f"created <= {epoch}"])
        if df.empty:
            data[data_source["name"]] = {}
            continue
        
        last_created = df["created"].max()
        df = df[df["created"] == last_created]
        
        df = df.groupby(["clusterid", "hostid"]).first().reset_index()

        # group by clusterid and get the count per clusterid
        cnt = df.groupby("clusterid")["clusterid"].count()
        # get clusterids with count > 1
        clusterids = cnt[cnt > 1].index
        # filter df by clusterids
        df = df[df["clusterid"].isin(clusterids)]

        data[data_source["name"]] = {}
        for clusterid in clusterids:
            data[data_source["name"]][clusterid] = {}
            for _, row in df[df["clusterid"] == clusterid].iterrows():
                group_name = row["group_name"]
                host_name = row["host_name"]
                if group_name not in data[data_source["name"]][clusterid]:
                    data[data_source["name"]][clusterid][group_name] = {}
                if host_name not in data[data_source["name"]][clusterid][group_name]:
                    data[data_source["name"]][clusterid][group_name][host_name] = []
                data[data_source["name"]][clusterid][group_name][host_name].append(row["itemid"])
 
    return data

if __name__ == "__main__":
    # read arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', type=str, help='config yaml file')
    parser.add_argument('--end', type=int, default=0, help='End epoch.')
    parser.add_argument('--output', type=str, default="", help='Output file.')

    # suppress python warnings
    import warnings
    warnings.filterwarnings("ignore")

    args = parser.parse_args()
    
    data = report(args.config, args.end)

    import json
    if args.output:
        with open(args.output, "w") as f:
            f.write(json.dumps(data, indent=4))
    else:
        print(json.dumps(data, indent=4))
    
