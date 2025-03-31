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
        viewer.prepare(config, "bycluster")

        
if __name__ == '__main__':
    unittest.main()