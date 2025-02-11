import unittest

import __init__
import trends_stats
import detector
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestDetector(unittest.TestCase):
    def _test_item(self, config_file, endep, itemId, expected_anomal=False):
        itemIds = [itemId]
        # first data load
        trends_stats.update_stats(config_file, endep, 0, initialize=True, itemIds=itemIds) 

        results = detector.run(config_file, endep, itemIds=itemIds, initialize=True)
        if expected_anomal:
            self.assertTrue(len(results["test_detector_many"]["anomaly_itemIds2"]) > 0)
        else:
            self.assertIsNone(results["test_detector_many"])


    def test_detector(self):
        name = 'test_detector_many'
        config_file = 'tests/test_detector_many.d/config.yml'
        config_loader.load_config(config_file)
        ms = ModelsSet(name)
        ms.initialize()

        endep = 1738022400

        # 56769 86815 141904

        self._test_item(config_file, endep, 57319, False) # ZIPSW004: Interface Gi1/0/16(VMSRV049 ZIP-A TB): Bits received
        self._test_item(config_file, endep, 82848, False) # near anomaly case: NFPSW001: Interface Gi1/0/8(): Bits sent
        self._test_item(config_file, endep, 86815, False) # near anomaly case: LABSW002: Interface Gi0/18(): Bits received
        self._test_item(config_file, endep, 227833, False) # many peaks
        



if __name__ == '__main__':
    unittest.main()