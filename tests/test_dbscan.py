import unittest

import __init__
import utils.config_loader as config_loader
import tests.testlib as testlib
import classifiers.dbscan as dbscan

class TestDbscan(unittest.TestCase):
    
    def test_dbscan(self):
        testlib.load_test_conf()
        name = 'test_dbscan'
        endep = 1739505598 
        conf = config_loader.conf
        conf["data_sources"] = {
            "csv_datasource": {
                "type": "csv",
                "data_dir": "testdata/csv/20250214_1100"
            },
        }
        config_loader.cascade_config("data_sources")
        itemIds = [59888, 93281, 94003, 110309, 141917, 217822, 236160, 217825, 270793, 270797, 217823]

        testlib.import_test_data(conf, itemIds, endep)
        clusters, centroids, chart_info = dbscan.classify_charts(
            conf,
            "csv_datasource",
            itemIds=itemIds,
            endep=endep,
        )
        self.assertEqual(len(centroids), 1)
        
        # number of itemIds in clusters whose value is 1
        count = sum(1 for cluster in clusters.values() if cluster == -1)
        self.assertEqual(count, 6)

        # number of itemIds in clusters whose value is 2
        count = sum(1 for cluster in clusters.values() if cluster == 1)
        self.assertEqual(count, 5)



if __name__ == '__main__':
    unittest.main()