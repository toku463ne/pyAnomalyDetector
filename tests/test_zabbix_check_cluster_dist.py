import unittest, os
import time

import __init__
import data_processing.detector as detector
import utils.config_loader as config_loader
import trends_stats
import check_conn
import viewer
import testlib

class TestZabbix(unittest.TestCase):
    def test_zabbix(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config_loader.load_config("tests/test_zabbix.d/config.yml")
        conf = config_loader.conf
        data_source = conf["data_sources"][0]
        
        d = detector.check_distance(data_source, 78030, 78019)
        self.assertGreater(d, 0)


if __name__ == '__main__':
    unittest.main()