import unittest, os
import time

import __init__

from data_getter.logan_getter import LoganGetter
from models.models_set import ModelsSet
import tests.testlib as testlib
import utils.config_loader as config_loader


class TestLoganGetter(unittest.TestCase):
    
    def test_logan_getter(self):
        testlib.load_test_conf()
        # csv data is in testdata/loganal/sophos
        # start a local server to serve the csv files
        os.system('cd testdata/loganal/test1 && python3 -m http.server 8200 &')
        os.system('cd testdata/loganal/test2 && python3 -m http.server 8201 &')
        time.sleep(1)
        name = 'test_logan_getter'
        data_source = {
            'name': name,
            'type': 'logan',
            'data_dir': '/tmp/anomdec_test',
            'base_url': 'http://localhost:8200/',
            'groups': {
                'proxy': {
                    1: {'name': 'proxy01', 'minimal_group_size': 100},
                    2: {'name': 'proxy02', 'minimal_group_size': 1000}
                },
                'firewall': {
                    3: {'name': 'fw01'},
                    4: {'name': 'fw02', 'base_url': 'http://localhost:8201/'},
                },
            },
            'minimal_group_size': 10000
        }
        config_loader.conf['data_sources'] = {}
        config_loader.conf['data_sources'][name] = data_source
        
        config_loader.cascade_config("data_sources")
        data_source = config_loader.conf['data_sources'][name]
        ms = ModelsSet(name)
        ms.initialize()
        # remove data_dir
        if os.path.exists(data_source['data_dir']):
            os.system('rm -rf %s' % data_source['data_dir'])
        
        data_source = config_loader.conf['data_sources'][data_source['name']]
        logan_getter = LoganGetter(data_source)
        self.assertIsNotNone(logan_getter)
        self.assertTrue(logan_getter.check_conn())
        
        
        # get itemIds
        itemIds = logan_getter.get_itemIds()
        self.assertGreater(len(itemIds), 0)

        endep = 1746108000
        startep = endep - 3600 * 3 + 1
        itemIds = [4174353215400002, 3174353218500022, 2174353226900002, 1174346710600004]
        
        # get history
        history = logan_getter.get_history_data(startep, endep, itemIds)
        self.assertIsNotNone(history)
        self.assertGreater(len(history), 0)

        got_itemIds = history['itemid'].unique()
        self.assertEqual(len(got_itemIds), len(itemIds))
        self.assertTrue(all(itemId in got_itemIds for itemId in itemIds))
        for itemId in itemIds:
            self.assertGreater(len(history[history["itemid"] == itemId]), 0)


        # get trends
        startep = endep - 3600 * 24 * 3
        
        trends = logan_getter.get_trends_data(startep, endep, itemIds)
        self.assertIsNotNone(trends)
        self.assertGreater(len(trends), 0)
        got_itemIds = trends['itemid'].unique()
        self.assertEqual(len(got_itemIds), len(itemIds))
        self.assertTrue(all(itemId in got_itemIds for itemId in itemIds))
        for itemId in itemIds:
            size = len(trends[trends["itemid"] == itemId])
            self.assertGreater(size, 0)


        trends_all = logan_getter.get_trends_full_data(startep, endep, itemIds)
        for itemId in itemIds:
            size = len(trends_all[trends_all["itemid"] == itemId])
            self.assertGreater(size, 0)


        details = logan_getter.get_items_details(itemIds)
        self.assertIsNotNone(details)
        self.assertEqual(len(details), 4)

        row = details[details["itemid"] == itemIds[0]]
        self.assertEqual(row["group_name"].values[0], "firewall")
        self.assertEqual(row["hostid"].values[0], 4)
        self.assertEqual(row["host_name"].values[0], "fw02")
        
        os.system('pkill -f http.server')



if __name__ == '__main__':
    unittest.main()