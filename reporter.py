from typing import Dict
import json

from models.models_set import ModelsSet
import utils.config_loader as config_loader
import utils
import data_getter

def report(conf: Dict, epoch: int) -> Dict:
    data = {}
    data_sources = conf["data_sources"]
    for data_source_name in data_sources:
        history_interval = conf['history_interval']
        history_retention = conf['history_retention']
        startep = epoch - history_interval * history_retention

        ms = ModelsSet(data_source_name)
        # get anomaly dataframe
        anom = ms.anomalies.get_data([f"created >= {startep}",
                                    f"created <= {epoch}"])
        
        anom = anom[["itemid", "hostid", "item_name", "host_name", "clusterid", "created"]]
        anom = anom.drop_duplicates(subset=["itemid"])

        if anom.empty:
            continue
        
        # group by hostid and clusterid and count per hostid and clusterid and show the first itemid
        anom = anom.groupby(["hostid", "clusterid"]).agg({"itemid": "first", "host_name": "first", "item_name": "first", "created": "first"}).reset_index()
        # only keep groups with more than 1 itemid
        anom = anom[anom["clusterid"] != -1]
        
        # group by clusterid and count
        ganom = anom.groupby(["clusterid"]).agg({"clusterid": "count"})
        ganom = ganom[ganom["clusterid"] > 1]

        clusterids = list(set(ganom.index.tolist()))
        # filter anom by clusterids
        anom = anom[anom["clusterid"].isin(clusterids)]
        
        # convert created(epoch) to YYYY-MM-DD HH:MM:SS
        anom["created"] = anom["created"].apply(lambda x: utils.epoch2str(x, "%Y-%m-%d %H:%M:%S"))
        anom["created"] = anom["created"].astype(str)

        # convert details to json
        anom_json = anom.set_index("itemid").to_json(orient="index")
        
        data[data_source_name] = json.loads(anom_json)
        
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
    err = None
    try:
        config = config_loader.load_config(args.config)
        
        data = report(config, args.end)
    except Exception as e:
        err = e
        import logging
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Error: {e}")
        if not args.output:
            raise
        
    if err is None:
        data["has_anomalies"] = "no"
        data["has_error"] = "no"
        for k, v in data.items():
            if k == "has_anomalies":
                continue
            if len(v) > 0:
                data["has_anomalies"] = "yes"
                break
    else:
        data = {}
        data["error"] = str(err)
        data["has_error"] = "yes"
        
    if args.output:
        with open(args.output, "w") as f:
            f.write(json.dumps(data, indent=4))
    else:
        print(json.dumps(data, indent=4))
    
