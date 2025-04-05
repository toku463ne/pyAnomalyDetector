"""
unit tests for utils.kmeans.py
"""
import unittest, os

import __init__
import tests.testlib as testlib
import utils.kmeans as kmeans
import utils.normalizer as normalizer

class TestKMeans(unittest.TestCase):
    # test kmeans
    def test_kmeans(self):
        base_clocks = normalizer.get_base_clocks(1732665600, 1735344000, 86400)
        chart_ids = [
            1730053933000000001, #1 .. a
            1730053959000000020, #2 .. b
            1730053960000000022, #2 .. c
            1730053933000000002, #3 .. d
            1730053933000000003, #3 .. e
        ]
        charts = kmeans.load_csv_metrics("tests/testdata/history.csv", base_clocks, chart_ids)
        op_charts = {}
        for chart_id in charts:
            op_charts[chart_id] = 1 - charts[chart_id]

        dist_a_b = kmeans.calculate_distance(charts[1730053933000000001], 
                                             op_charts[1730053933000000001], 
                                             charts[1730053959000000020])
       
        print("dist_a_b: ", dist_a_b)

        dist_b_c = kmeans.calculate_distance(charts[1730053959000000020], 
                                             op_charts[1730053959000000020], 
                                             charts[1730053960000000022])
        print("dist_b_c: ", dist_b_c)

        dist_c_d = kmeans.calculate_distance(charts[1730053960000000022], 
                                             op_charts[1730053960000000022], 
                                             charts[1730053933000000002])
        print("dist_c_d: ", dist_c_d)
        dist_d_e = kmeans.calculate_distance(charts[1730053933000000002], 
                                             op_charts[1730053933000000002], 
                                             charts[1730053933000000003])
        print("dist_d_e: ", dist_d_e)

if __name__ == '__main__':
    unittest.main()

