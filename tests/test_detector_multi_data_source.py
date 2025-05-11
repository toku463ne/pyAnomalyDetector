import unittest

import __init__
from models.models_set import ModelsSet
import utils.config_loader as config_loader
import detect_anomalies
import trends_stats
import reporter
import tests.testlib as testlib


class TestDetector(unittest.TestCase):    
    def test_detect_all(self):
        testlib.load_test_conf()
        config = config_loader.conf
        config['data_sources'] = {}
        config['data_sources']['test_multi_mysql'] = {
                'data_dir': "testdata/csv/20250508/mysql",
                'type': 'csv'
            }
        config['data_sources']['test_multi_psql'] = {
                'data_dir': "testdata/csv/20250508/psql",
                'type': 'csv'
            }
        config_loader.cascade_config('data_sources')
        
        data_source_names = ['test_multi_mysql', 'test_multi_psql']
        expected_mysql_itemIds = [69508,75428,75428,72820,72820,72821,72821,75428,75428,72820,72820,72821,72821,75382,
                                  75382,75427,75427,75428,75428]
        expected_psql_itemIds = [266919,266919,266920,266920,141292,141413,141743,230843,230844,230845,141743,230991,
                                 256679,256681,256679,256681,256679,256681,256679,256681,282047,256679,256681,256804,
                                 141262,224318,240319,240322,240323,240326,240328,240333,240334,240338,256679,256681,
                                 256802,256804,271738,224318,240319,240322,240323,240326,240333,240334,240338,256679,
                                 256681,233974,235357]
        for data_source_name in data_source_names:
            ms = ModelsSet(data_source_name)
            ms.initialize()
        
        itemIds = []
        endep = 1746600901 - 3600*24
        trends_stats.update_stats(config, endep, 0, itemIds=itemIds, initialize=True)
        
        for data_source_name in data_source_names:
            ms = ModelsSet(data_source_name)
            df = ms.trends_stats.read_stats()
            self.assertGreater(len(df), 0)
            if data_source_name == 'test_multi_mysql':
                # expected_mysql_itemIds must be included in df.itemid
                self.assertTrue(all(itemId in df.itemid.tolist() for itemId in expected_mysql_itemIds))
            elif data_source_name == 'test_multi_psql':
                # expected_psql_itemIds must be included in df.itemid
                self.assertTrue(all(itemId in df.itemid.tolist() for itemId in expected_psql_itemIds))

        # detect anomalies
        endep = 1746600901
        anomalies = detect_anomalies.run(config, endep)

        self.assertGreater(len(anomalies), 0)

        # import anomalies
        ms = ModelsSet('test_multi_mysql')
        ms.anomalies.import_data('testdata/csv/20250508/mysql/anomalies.csv.gz')
        ms = ModelsSet('test_multi_psql')
        ms.anomalies.import_data('testdata/csv/20250508/psql/anomalies.csv.gz')        

        # classify charts
        detect_anomalies.classify_charts(endep)

        for data_source_name in data_source_names:
            ms = ModelsSet(data_source_name)
            df = ms.anomalies.get_data()
            self.assertGreater(len(df), 0)
            self.assertGreater(len(df[df.clusterid > 0]), 0)

        result = reporter.report(config, endep)
        self.assertEqual(len(result["test_multi_mysql"]), 3)



if __name__ == '__main__':
    unittest.main()

    # streamlit run /home/ubuntu/git/pyAnomalyDetector2/tests/test_detector_detect2.py

