
from models.models_set import ModelsSet

def notify(config_file: str, data_file: str, epoch: int):
    data = {}
    with open(data_file, "r") as f:
        data = json.load(f)    

    config_loader.load_config(config_file)
    conf = config_loader.conf
    data_sources = conf['data_sources']

    anomaly_cache_ep = epoch - conf['anomaly_cache_period']

    for data_source in data_sources:
        data_source_name = data_source["name"]
        ms = ModelsSet(data_source["name"])

        
        target_itemIds = []
        # filter cluster classes having multiple hosts
        clusters = data[data_source_name]["clusters"]
        for cluster in clusters.values():
            if len(cluster) > 1:
                for itemIds in cluster.values():
                    target_itemIds.append(itemIds[0])
        
        # rule out items in the recent_anomalies table
        filtered_itemIds = ms.recent_anomalies.filter_itemIds(target_itemIds, anomaly_cache_ep)

        anomaly_itemIds2 = data[data_source_name]["anomaly_itemIds2"]
        # update recent_anomalies table
        for itemId in anomaly_itemIds2:
            ms.recent_anomalies.upsert(itemid, epoch)

        # delete old cache
        ms.recent_anomalies.delete_old_entries(anomaly_cache_ep)

