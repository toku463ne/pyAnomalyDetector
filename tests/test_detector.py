import unittest

import __init__
import stats
import anomaly_detector
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestDetector(unittest.TestCase):
    def test_detector(self):
        name = 'test_detector'
        config_file = 'tests/test_detector.d/config.yml'
        config_loader.load_config(config_file)

        ms = ModelsSet(name)
        ms.initialize()

        endep = 1731596400 # Fri Nov 15 00:00:00 JST 2024
        
        # first data load
        stats.update_stats(config_file, endep, 0, initialize=True)

        results = anomaly_detector.run(config_file, endep)
        self.assertTrue(len(results) > 0)
        self.assertTrue(len(results[name]["clusters"]) > 0)
        self.assertTrue(len(results[name]["clusters"][0]["itemIds"]) > 0)
        self.assertTrue(len(results[name]["clusters"][0]["hostIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds"]) > 0)
        self.assertTrue(len(results[name]["anomaly_itemIds2"]) > 0)

        

        




if __name__ == '__main__':
    unittest.main()