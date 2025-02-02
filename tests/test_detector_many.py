import unittest

import __init__
import stats
import detector
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestDetector(unittest.TestCase):
    def test_detector(self):
        name = 'test_detector_many'
        config_file = 'tests/test_detector_many.d/config.yml'
        config_loader.load_config(config_file)

        ms = ModelsSet(name)
        ms.initialize()

        endep = 1738022400 - 3600
        group_names = ['app/imt', 'app/bcs', 'app/cal', 'app/iim', 'app/sim', 'hw/nw', 'hw/pc']
        
        # first data load
        stats.update_stats(config_file, endep, 0, initialize=True)

        results = detector.run(config_file, endep, group_names=group_names, initialize=True)
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results[name]["clusters"]) > 0)
        self.assertTrue(len(results[name]["clusters"][3]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        import json
        json.dump(results, open('tests/test_detector_many.d/results_1st.json', 'w'), indent=2)

        # read history data
        history_df = ms.history.get_data()
        self.assertTrue(len(history_df) > 0)
        h_startep1 = int(history_df['clock'].min())
        h_endep1 = int(history_df['clock'].max())
        startep1 = ms.history_updates.get_startep()
        endep1 = ms.history_updates.get_endep()
        self.assertEqual(endep1, endep)

        self.assertEqual(len(history_df[history_df['itemid'] == 23274]), 12)

        endep = 1737791212
        results = detector.run(config_file, endep, group_names=group_names, initialize=False)
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        # read history data
        history_df = ms.history.get_data()
        self.assertTrue(len(history_df) > 0)
        h_startep2 = int(history_df['clock'].min())
        h_endep2 = int(history_df['clock'].max())
        startep2 = ms.history_updates.get_startep()
        endep2 = ms.history_updates.get_endep()
        self.assertEqual(endep2, endep)

        self.assertEqual(len(history_df[history_df['itemid'] == 23274]), 12)

        self.assertGreater(h_endep2, h_endep1)
        self.assertGreater(endep2, endep1)
        self.assertGreater(startep2, startep1)
        self.assertGreater(h_startep2, h_startep1)
        
        json.dump(results, open('tests/test_detector_many.d/results_2nd.json', 'w'), indent=2)





if __name__ == '__main__':
    unittest.main()