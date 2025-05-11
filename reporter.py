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
        if anom.empty:
            continue
        anom2 = anom.copy()
        
        itemIds = list(set(anom["itemid"].tolist()))
        data_source = data_sources[data_source_name]
        dg = data_getter.get_data_getter(data_source)
        details = dg.get_items_details(itemIds)

        # left join anom and details
        anom = anom.merge(details, how="left", on=["itemid", "hostid", "item_name", "host_name", "group_name"])

        # group by hostid and clusterid and count per hostid and clusterid and show the first itemid
        anom = anom.groupby(["hostid", "clusterid"]).agg({"itemid": ["count", "first"]}).reset_index()
        # only keep groups with more than 1 itemid
        anom = anom[anom["clusterid"] != -1]
        anom = anom[anom["itemid"]["count"] > 1]

        itemIds = list(set(anom["itemid"]["first"].apply(int).tolist()))
        details = details[details["itemid"].isin(itemIds)]
        details = details.merge(anom2, how="inner", on=["itemid", "hostid", "item_name", "host_name", "group_name"])
        details = details.drop_duplicates(subset=["itemid"])

        # convert created(epoch) to YYYY-MM-DD HH:MM:SS
        details["created"] = details["created"].apply(lambda x: utils.epoch2str(x, "%Y-%m-%d %H:%M:%S"))
        details["created"] = details["created"].astype(str)

        details = details[["itemid", "hostid", "item_name", "host_name", "group_name", "created", "clusterid"]]

        # convert details to json
        details_json = details.set_index("itemid").to_json(orient="index")
        
        data[data_source_name] = json.loads(details_json)
        
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
    
