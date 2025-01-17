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

        endep = 1731596400 # Fri Nov 15 00:00:00 JST 2024
        
        # first data load
        stats.update_stats(config_file, endep, 0, initialize=True)
        
        # check trends
        df = ms.trends_stats.read_stats()
        self.assertEqual(len(df), 16)
        self.assertGreater(df['mean'].sum(), 0)
        self.assertGreater(df['std'].sum(), 0)

        # second data load
        endep += 3600*24*2
        stats.update_stats(config_file, endep, 0, initialize=False)
        self.assertEqual(len(df), 16)
        self.assertGreater(df['mean'].sum(), 0)
        self.assertGreater(df['std'].sum(), 0)


if __name__ == '__main__':
    unittest.main()