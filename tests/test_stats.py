import unittest

import __init__
import stats
from models.models_set import ModelsSet
import utils.config_loader as config_loader

class TestStats(unittest.TestCase):
    def test_stats(self):
        name = 'test_stats'
        config_file = 'tests/test_stats.d/config.yml'
        config_loader.load_config(config_file)
        ms = ModelsSet(name)
        ms.initialize()
        itemIds = [23274,33026,242424,242425,255260,61466,61472,61618,247790,57382]

        endep = 1737791212 - 3600*24*2
        
        # first data load
        stats.update_stats(config_file, endep, 0, itemIds=itemIds, initialize=True)
        
        # check trends
        df = ms.trends_stats.read_stats()
        self.assertEqual(len(df), 10)
        self.assertGreater(df['mean'].sum(), 0)
        self.assertGreater(df['std'].sum(), 0)

        

        cnt = int(df[df['itemid'] == 23274]['cnt'][0])
        self.assertGreater(cnt, 0)

        lastep = ms.trends_updates.get_endep()
        self.assertGreater(lastep, 0)
        startep = ms.trends_updates.get_startep()
        self.assertGreater(startep, 0)

        # second data load
        endep = 1737791212
        stats.update_stats(config_file, endep, 0, itemIds=itemIds, initialize=False)
        df = ms.trends_stats.read_stats()
        self.assertEqual(len(df), 10)
        cnt2 = int(df[df['itemid'] == 23274]['cnt'][0])
        self.assertGreater(cnt2, 0)
        self.assertEqual(cnt, cnt2)

        lastep2 = ms.trends_updates.get_endep()
        self.assertGreater(lastep2, lastep)
        startep2 = ms.trends_updates.get_startep()
        self.assertGreater(startep2, startep)


if __name__ == '__main__':
    unittest.main()