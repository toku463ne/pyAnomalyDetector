"""
unit tests for sample_getter.py
"""
import unittest, os

import __init__

from data_getter.sample_getter import SampleGetter


class TestSampleGetter(unittest.TestCase):

    def test_sample_getter(self):
        data_source = {
            'type': 'sample',
            'sample_config': 'sample1.yml',
            'seed': 1
        }
        sample_getter = SampleGetter(data_source)
        self.assertIsNotNone(sample_getter)

        startep = 1730386800
        endep = 1731596400
        itemIds = [1,2]
        data = sample_getter.get_trends_data(startep, endep, itemIds)
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 672)

        # test itemIds in the data
        got_itemIds = data['itemid'].unique()
        self.assertEqual(len(got_itemIds), 2)
        self.assertEqual(got_itemIds[0], 1)
        self.assertEqual(got_itemIds[1], 2)




if __name__ == '__main__':
    unittest.main()