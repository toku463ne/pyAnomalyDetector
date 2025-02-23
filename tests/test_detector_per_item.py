import unittest

import __init__
import trends_stats
import detector
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestDetector(unittest.TestCase):
    def _test_item(self, name, config_file, endep, itemId, expected_anomal=False):
        itemIds = [itemId]
        # first data load
        trends_stats.update_stats(config_file, endep, 0, initialize=True, itemIds=itemIds) 

        results = detector.run(config_file, endep, itemIds=itemIds, initialize=True)
        df = results[name]
        if df is None: 
            self.assertTrue(not expected_anomal)
            return
        df = df[df['itemid'] == itemId]
        if expected_anomal:
            self.assertTrue(len(df) > 0)
        else:
            self.assertTrue(len(df) == 0)


    def test_detector(self):
        name = 'test_detector_many'
        config_file = 'tests/test_detector_many.d/config.yml'
        config_loader.load_config(config_file)
        ms = ModelsSet(name)
        ms.initialize()

        endep = 1739498400 # Fri Feb 14 11:00:00 AM JST 2025
        self._test_item(name, config_file, endep, 255218, True)
        self._test_item(name, config_file, endep, 141917, False)
        self._test_item(name, config_file, endep, 236160, False)
        



if __name__ == '__main__':
    unittest.main()