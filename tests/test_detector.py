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
        self.assertTrue(len(results[name]["clusters"]) > 0)
        self.assertTrue(len(results[name]["clusters"][0]["itemIds"]) > 0)
        self.assertTrue(len(results[name]["clusters"][0]["hostIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        

        




if __name__ == '__main__':
    unittest.main()