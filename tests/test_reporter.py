"""
unit tests for zabbix_dashboard.py
"""
import unittest

import __init__
from models.models_set import ModelsSet
import __init__
import reporter

class TestReporter(unittest.TestCase):  
    def test_reporter(self):
        config = "tests/test_reporter.d/config.yml"
        data_file = "tests/test_reporter.d/results_1st.json"
        reporter.report(config, data_file, 0)

        ms = ModelsSet("test_reporter")
        df = ms.recent_anomalies.get_all()
        print(df)

if __name__ == '__main__':
    unittest.main()