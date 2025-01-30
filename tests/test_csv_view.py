import unittest

import __init__
import viewer

class TestCsvView(unittest.TestCase):
    def test_csv_view(self):
        config = "tests/test_csv_view.d/config.yml"
        viewer.prepare(config, "tests/test_zabbix.d/result.json")
        





if __name__ == '__main__':
    unittest.main()