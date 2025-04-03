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
        charts = kmeans.load_csv_metrics("tests/testdata/history.csv", base_clocks)
        clusters, centroids = kmeans.run_kmeans(charts, 10, 0.5, 100, 10)
        self.assertEqual(len(clusters), 100)
        self.assertGreater(len(centroids), 10)

        # remove cluster with cluster_id == -1
        clusters = [c for c in clusters if c['cluster_id'] != -1]
        charts = [c for c in charts if c['cluster_id'] != -1]

        score = kmeans.evaluate_clusters(charts, clusters)
        self.assertGreater(score, 0.5)

        kmeans.process_clusters(charts, clusters)
        kmeans.plot_clusters(charts, clusters)




if __name__ == '__main__':
    unittest.main()

