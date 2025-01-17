"""
unit tests for sample_getter.py
"""
import unittest, os
import time

import __init__

from data_getter.zabbix_getter import ZabbixGetter


class TestZabbixGetter(unittest.TestCase):

    def test_zabbix_getter(self):
        data_source = {
            'type': 'psql',
            'host': 'localhost',
            'dbname': 'zabbix',
            'user': 'zabbix',
            'password': 'zabbix'
        }
        zabbix_getter = ZabbixGetter(data_source)
        self.assertIsNotNone(zabbix_getter)

        # get current epoch as endep
        endep = int(time.time())

        # get epoch 1 day ago as startep
        startep = endep - 86400

        # get itemIds
        itemIds = zabbix_getter.get_itemIds()
        self.assertIsNotNone(itemIds)
        self.assertTrue(len(itemIds) > 0)

        # get itemIds by item names
        itemIds = zabbix_getter.get_itemIds(item_names=['CPU*'])
        self.assertIsNotNone(itemIds)
        self.assertTrue(len(itemIds) > 0)

        # get itemIds by host names
        itemIds = zabbix_getter.get_itemIds(host_names=['Zabbix*'])
        self.assertIsNotNone(itemIds)
        self.assertTrue(len(itemIds) > 0)

        # get itemIs by host groups
        itemIds = zabbix_getter.get_itemIds(group_names=['Zabbix*'])
        self.assertIsNotNone(itemIds)
        self.assertTrue(len(itemIds) > 0)


        itemIds = itemIds[:100]
        
        data = zabbix_getter.get_history_data(startep, endep, itemIds)
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)

        data = zabbix_getter.get_trends_data(startep, endep, itemIds)
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)

        
if __name__ == '__main__':
    unittest.main()