from typing import Dict

from models.models_set import ModelsSet
import utils.config_loader as config_loader
import data_getter

def report(conf: Dict, epoch: int) -> Dict:
    anomaly_keep_secs = epoch - conf['anomaly_keep_secs']
    data = {}
    data_sources = conf["data_sources"]
    for data_source_name in data_sources:
        ms = ModelsSet(data_source_name)
        # get anomaly dataframe
        anom = ms.anomalies.get_data([f"created >= {anomaly_keep_secs}",
                                    f"created <= {epoch}"])
        if anom.empty:
            continue
        
        data_source = data_sources[data_source_name]
        dg = data_getter.get_data_getter(data_source)
        details = dg.get_items_details()

        # left join anom and details
        anom = anom.merge(details, how="left", on=["itemid", "hostid", "item_name", "host_name", "group_name"])

        # group by hostid and clusterid and count per hostid and clusterid and show the first itemid
        anom = anom.groupby(["hostid", "clusterid"]).agg({"itemid": ["count", "first"]}).reset_index()
        # only keep groups with more than 1 itemid
        anom = anom[anom["itemid"]["count"] > 1]

        itemIds = list(set(anom["itemid"]["first"].apply(int).tolist()))
        details = details[details["itemid"].isin(itemIds)]

        # convert details to json
        details_json = details.set_index("itemid").to_json(orient="index")
        
        data[data_source_name] = details_json
        
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
    config = config_loader.load_config(args.config)
    
    data = report(config, args.end)
    
    data["has_anomalies"] = "no"
    if len(data) > 0:
        for k, v in data.items():
            if k == "has_anomalies":
                continue
            if len(v) > 0:
                data["has_anomalies"] = "yes"
                break
    
    import json
    if args.output:
        with open(args.output, "w") as f:
            f.write(json.dumps(data, indent=4))
    else:
        print(json.dumps(data, indent=4))
    
