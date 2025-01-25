"""
unit tests for zabbix_dashboard.py
"""
import unittest
import os

import __init__
import viewer

class TestZabbixDashboard(unittest.TestCase):  
    def test_zabbix_dashboard(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config = "tests/test_zabbix.d/config.yml"
        data_file = "tests/test_zabbix.d/result.json"
        data_file = "/tmp/anom.json"
        viewer.prepare(config, data_file)

        
if __name__ == '__main__':
    unittest.main()