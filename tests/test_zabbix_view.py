import unittest, os
import time

import __init__
import viewer
import testlib

class TestZabbix(unittest.TestCase):
    def test_zabbix(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config = "tests/test_zabbix.d/config.yml"
        viewer.prepare(config)


if __name__ == '__main__':
    unittest.main()