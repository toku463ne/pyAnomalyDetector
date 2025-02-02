import json

from models.models_set import ModelsSet
import utils.config_loader as config_loader
import data_getter

def report(config_file: str, data_file: str, epoch: int):
    data = {}
    with open(data_file, "r") as f:
        data = json.load(f)    

    """
    data = {
  "test_detector_many": {
    "clusters": {
      "4": {
        "11637": [
          234021
        ]
      },
      "2": {
        "11637": [
          234023
        ]
      },
      "9": {
        "10620": [
          62378
        ]
      },
      "5": {
        "11634": [
          232910
        ]
      },
      "10": {
        "11284": [
          210003
        ]
      },
      "0": {
        "12042": [
          344598
        ]
      },
      "11": {
        "11285": [
          183351
        ]
      },
      "12": {
        "12033": [
          342336
        ]
      },
      "13": {
        "12033": [
          342338
        ]
      },
      "7": {
        "12033": [
          342342
        ]
      },
      "14": {
        "11637": [
          234027
        ]
      },
      "8": {
        "11450": [
          223603
        ]
      },
      "3": {
        "11450": [
          223605
        ]
      },
      "1": {
        "11838": [
          263766
        ]
      },
      "15": {
        "11284": [
          240407
        ]
      },
      "6": {
        "12042": [
          344602
        ]
      }
    },
    "groups": {
      "app/imt": [],
      "app/bcs": [],
      "app/cal": [
        240407,
        210003,
        183351
      ],
      "app/iim": [
        62378
      ],
      "app/sim": [
        263766,
        344598,
        344602
      ],
      "hw/nw": [],
      "hw/pc": [
        223603,
        223605,
        232910,
        234021,
        234023,
        234027,
        342336,
        342338,
        342342
      ]
    }
    }
    """

    config_loader.load_config(config_file)
    conf = config_loader.conf

    anomaly_cache_ep = epoch - conf['anomaly_cache_period']

    for data_source_name in data:
        data_source = conf["data_sources"][data_source_name]
        data_source["name"] = data_source_name
        ms = ModelsSet(data_source_name)
        dg = data_getter.get_data_getter(data_source)
        
        target_itemIds = []
        # filter cluster classes having multiple hosts
        clusters = data[data_source_name]["clusters"]
        for cluster in clusters.values():
            if len(cluster) > 1:
                for itemIds in cluster.values():
                    target_itemIds.append(itemIds[0])
        
        # rule out items in the recent_anomalies table
        filtered_itemIds = ms.recent_anomalies.filter_itemIds(target_itemIds, anomaly_cache_ep)

        """
        create json in the following format having filtered_itemIds
        {
            '<group_name>': {
              '<host_name>': [
                <item_id>, ...
              ]
            }
        }    
        """
        filtered_groups = {}
        groups = data[data_source_name]["groups"]
        item_hosts = dg.get_item_host_dict(filtered_itemIds)

        for group_name, itemIds in groups.items():
            filtered_groups[group_name] = {}
            for itemId in itemIds:
                if itemId not in filtered_itemIds:
                    continue

                host_name = item_hosts[itemId]
                if host_name not in filtered_groups[group_name]:
                    filtered_groups[group_name][host_name] = []
                filtered_groups[group_name][host_name].append(itemId)

        report_path = conf.get("report_path", "")
        if report_path:
            with open(f"{report_path}/{data_source_name}_filtered", "w") as f:
                json.dump(filtered_groups, f)
        else:
            # pretty print
            print(json.dumps(filtered_groups, indent=2))


        anomaly_itemIds2 = data[data_source_name]["anomaly_itemIds2"]
        # update recent_anomalies table
        for itemId in anomaly_itemIds2:
            ms.recent_anomalies.upsert(itemId, epoch)

        # delete old cache
        ms.recent_anomalies.delete_old_entries(anomaly_cache_ep)

