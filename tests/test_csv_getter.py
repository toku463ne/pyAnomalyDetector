"""
unit tests for sample_getter.py
"""
import unittest, os
import time

import __init__

from data_getter.csv_getter import CsvGetter


class TestCsvGetter(unittest.TestCase):
    def test_csv_getter(self):
        data_source = {
            'type': 'csv',
            'data_dir': 'tests/testdata/csv/20250204'
        }
        csv_getter = CsvGetter(data_source)
        self.assertIsNotNone(csv_getter)

        # check connection
        self.assertTrue(csv_getter.check_conn())

        endep = 1738022400
        trend_startep = endep - 3600 * 12
        
        # get trends data
        itemIds = [226604,226606,226610]
        df = csv_getter.get_trends_data(trend_startep, endep, itemIds)
        self.assertEqual(len(df["itemid"].unique()), 3)

        history_startep = endep - 3600 * 3
        # get history data
        df = csv_getter.get_history_data(history_startep, endep, itemIds)
        self.assertEqual(len(df["itemid"].unique()), 3)

        # classify itemIds by groups
        group_names = ['app/iim', 'app/sim', 'app/cal', 'app/bcs', 'hw/nw', 'hw/pc']
        groups = csv_getter.classify_by_groups(itemIds, group_names)
        self.assertEqual(len(groups), 6)
        self.assertEqual(len(groups['app/iim']), 0)
        self.assertEqual(len(groups['hw/nw']), 0)
        self.assertEqual(len(groups['hw/pc']), 3)

        
if __name__ == '__main__':
    unittest.main()