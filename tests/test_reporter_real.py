"""
unit tests for zabbix_dashboard.py
"""
import unittest
import pandas as pd
import time, os

import __init__
from models.models_set import ModelsSet
import utils.config_loader as config_loader
import reporter

class TestReporter(unittest.TestCase):  
    def test_reporter(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config_file = "tests/test_zabbix.d/config.yml"
        config_loader.load_config(config_file)
        
        endep = int(time.time() - 300)
        result = reporter.report(config_file, endep)

        result["has_anomalies"] = "no"
        if len(result) > 0:
            for k, v in result.items():
                if k == "has_anomalies":
                    continue
                if len(v) > 0:
                    result["has_anomalies"] = "yes"
                    break
        print(result)
        


if __name__ == '__main__':
    unittest.main()