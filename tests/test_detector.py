import unittest

import __init__
import stats
import detector
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestDetector(unittest.TestCase):
    def test_detector(self):
        name = 'test_detector'
        config_file = 'tests/test_detector.d/config.yml'
        config_loader.load_config(config_file)

        ms = ModelsSet(name)
        ms.initialize()

        endep = 1737791212 - 3600
        itemIds = [23274,33026,242424,242425,255260,61466,61472,61618,247790,57382]
        
        # first data load
        stats.update_stats(config_file, endep, 0, itemIds=itemIds, initialize=True)

        results = detector.run(config_file, endep, itemIds=itemIds, initialize=True)
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        #self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        # read history data
        history_df = ms.history.get_data(itemIds)
        self.assertTrue(len(history_df) > 0)
        h_startep1 = int(history_df['clock'].min())
        h_endep1 = int(history_df['clock'].max())
        startep1 = ms.history_updates.get_startep()
        endep1 = ms.history_updates.get_endep()
        self.assertEqual(endep1, endep)

        self.assertEqual(len(history_df[history_df['itemid'] == 23274]), 12)

        endep = 1737791212
        results = detector.run(config_file, endep, itemIds=itemIds, initialize=False)
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        #self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        # read history data
        history_df = ms.history.get_data(itemIds)
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
        




if __name__ == '__main__':
    unittest.main()