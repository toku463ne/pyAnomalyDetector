import unittest

import __init__
import utils.config_loader as config_loader
import tests.testlib as testlib
import classifiers.dbscan as dbscan

class TestDbscan(unittest.TestCase):
    
    def test_dbscan(self):
        testlib.load_test_conf()
        name = 'test_dbscan3'
        endep = 1747536901 
        conf = config_loader.conf
        conf["data_sources"] = {
            "csv_datasource": {
                "type": "csv",
                "data_dir": "testdata/csv/20250518"
            },
        }
        config_loader.cascade_config("data_sources")
        #itemIds = [237971, 238193, 240506, 282003, 282047]
        # must be group of 237971, 238193, 240506, (282003, 282047)
        itemIds = []

        testlib.import_test_data(conf, itemIds, endep)
        clusters, centroids, chart_info = dbscan.classify_charts(
            conf,
            "csv_datasource",
            itemIds=itemIds,
            endep=endep,
        )
        self.assertEqual(len(centroids), 6)
        
        # number of itemIds in clusters whose value is -1
        count = sum(1 for cluster in clusters.values() if cluster == -1)
        self.assertEqual(count, 18)

        # number of itemIds in clusters whose value is 6
        count = sum(1 for cluster in clusters.values() if cluster == 6)
        self.assertEqual(count, 6)


if __name__ == '__main__':
    unittest.main()