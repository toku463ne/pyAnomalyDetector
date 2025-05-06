import unittest
import time

import __init__
import trends_stats
from models.models_set import ModelsSet
import data_getter
import testlib
import trends_stats
import detect_anomalies

class TestTrendsStats(unittest.TestCase):        
    def test_stats(self):
        name = 'detect1_zbx_psql'
        config = testlib.load_config("samples/zabbix_psql.yml")
        data_source_name = "zb10"
        data_source = config["data_sources"][data_source_name]
        dg = data_getter.get_data_getter(data_source)

        itemIds = []
        for cond in data_source["item_conds"]:
            itemIds.extend(dg.get_itemId_by_cond(cond["filter"], limit=10))
        for cond in data_source["item_diff_conds"]:
            itemIds.extend(dg.get_itemId_by_cond(cond["filter"], limit=10))

        self.assertGreater(len(itemIds), 0)
        
        ms = ModelsSet(data_source_name)
        ms.initialize()
        endep = time.time() - 600
        trends_stats.update_stats(config, endep, itemIds=itemIds, initialize=True, max_itemIds=100)
        stats_df = ms.trends_stats.read_stats()
        self.assertGreater(len(stats_df), 0)

        detect_anomalies.init(config)
        detect_anomalies.run(config, itemIds=itemIds, max_itemIds=100, detection_stages=[1])

        hist_df = ms.history_stats.read_stats()
        self.assertGreater(len(hist_df), 0)

        hist = ms.history.get_data(itemIds)
        self.assertEqual(len(hist), 0)





if __name__ == '__main__':
    unittest.main()