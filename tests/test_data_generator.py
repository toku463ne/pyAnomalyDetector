"""
unittest for utils.data_generator.py
"""
import numpy as np
import unittest

import __init__
from utils.data_generator import *

class TestDataGenerator(unittest.TestCase):
    def test_sine_wave(self):
        y = sine_wave(0, 10, 4, 1, 0)
        self.assertEqual(len(y), 4)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertEqual(y[0], 5)
        
        y = sine_wave(0, 10, 8, 2, 0)
        self.assertEqual(len(y), 8)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertEqual(y[0], 5)

        y = sine_wave(0, 10, 4, 1, 1)
        self.assertEqual(len(y), 4)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertEqual(y[0], 10)
        
        y = sine_wave(0, 10, 8, 2, 1)
        self.assertEqual(len(y), 8)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertGreater(y[0]+0.1, 10)

    
    def test_normal_distribution_wave(self):
        y = normal_distribution_wave(0, 10, 4, 1, 0, 1, 0)
        self.assertEqual(len(y), 4)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertEqual(y[0], 0)
        
        y = normal_distribution_wave(0, 10, 8, 2, 0, 1, 0)
        self.assertEqual(len(y), 8)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertEqual(y[0], 0)

        y = normal_distribution_wave(0, 10, 4, 1, 0, 1, 1)
        self.assertEqual(len(y), 4)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertGreater(y[0]+1, 5)
        self.assertLess(y[0]-1, 5)
        
        y = normal_distribution_wave(0, 10, 8, 2, 0, 1, 1)
        self.assertEqual(len(y), 8)
        self.assertGreaterEqual(min(y),0)
        self.assertLessEqual(max(y),10)
        self.assertGreater(y[0]+1, 5)
        self.assertLess(y[0]-1, 5)


    def test_merge_data(self):
        data1 = np.array([1, 2, 3])
        data2 = np.array([4, 5, 6])
        merged_data = merge_data(data1, data2)
        self.assertTrue(np.array_equal(merged_data, np.array([5, 7, 9])))

    

if __name__ == '__main__':
    unittest.main()