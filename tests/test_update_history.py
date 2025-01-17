import unittest
import warnings

import __init__
import data_processing.history as history
from models.models_set import ModelsSet
import utils.config_loader as config_loader
import utils.normalizer as normalizer
from matplotlib import MatplotlibDeprecationWarning

class TestUpdateHistory(unittest.TestCase):
    def test_update_history(self):
        name = 'test_update_history'
        config_file = 'tests/test_update_history.d/config.yml'
        config_loader.load_config(config_file)
        conf = config_loader.conf
        data_source = conf['data_sources'][0]
        ms = ModelsSet(name)
        ms.initialize()
        
        # get base clocks
        org_startep = 1730386800 # Fri Nov  1 00:00:00 JST 2024
        startep = org_startep
        endep = 1730386800 + 3600*3 -1
        base_clocks = normalizer.get_base_clocks(startep, endep, 600)
        
        # first update (initialize)
        history.update_history(data_source, [], base_clocks, 0)

        # check history
        df = ms.history.get_data([])
        self.assertEqual(len(df), 16*18)
        self.assertGreater(df['value'].sum(), 0)

        # first clock of itemid=1
        self.assertEqual(df[(df['itemid'] == 1)]['clock'].values[0], base_clocks[0])

        # last clock of itemid=1
        self.assertEqual(df[(df['itemid'] == 1)]['clock'].values[-1], base_clocks[-1])


        # second update
        startep = endep+1
        endep += 3600
        oldep = org_startep + 3600 
        base_clocks = normalizer.get_base_clocks(startep, endep, 600)
        base_clocks = base_clocks[1:]
        base_clocks.append(base_clocks[-1] + 600)
        history.update_history(data_source, [], base_clocks, oldep)

        # check history
        df = ms.history.get_data([])
        self.assertEqual(len(df), 16*18)
        self.assertGreater(df['value'].sum(), 0)

        # first clock of itemid=1
        self.assertEqual(df[(df['itemid'] == 1)]['clock'].values[0], oldep)

        # last clock of itemid=1
        self.assertEqual(df[(df['itemid'] == 1)]['clock'].values[-1], base_clocks[-1])

        

if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)

    unittest.main()