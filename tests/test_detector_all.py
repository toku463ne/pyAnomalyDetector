import unittest

import __init__
from models.models_set import ModelsSet
import utils.config_loader as config_loader
import detect_anomalies
import trends_stats
import tests.testlib as testlib

detection_stages = [
    detect_anomalies.STAGE_DETECT1,
    detect_anomalies.STAGE_DETECT4]

class TestDetector(unittest.TestCase):
    
    def test_detect_all(self):
        testlib.load_test_conf()
        name = 'test_detect_all'
        config = config_loader.conf
        config['data_sources'] = {}
        config['data_sources'][name] = {
                'data_dir': "testdata/csv/20250214_1100",
                'type': 'csv',
                'batch_size': 1000,
                'trends_interval': 86400,
                'trends_retention': 14,
                'trends_min_count': 14,
                'long_trends_retention': 60,
                'long_trends_min_count': 40,
                'detect1_lambda_threshold': 3.0,
                'detect2_lambda_threshold': 2.0,
                'detect3_lambda_threshold1': 1.0,
                'detect3_lambda_threshold2': 2.0,
                'ignore_diff_rate': 0.2, # ignore if the peaks are just less than this rate
                'anomaly_valid_count_rate': 0.8, # valid anomaly if the count is more than this rate
                'anomaly_keep_secs': 86400, # 1day  
                'history_interval': 600,
                'history_retention': 18,
                'history_recent_retention': 6
            }
        ms = ModelsSet(name)
        ms.initialize()
        
        
        itemIds = []

        endep = 1739505598 - 3600*24*3
        trends_stats.update_stats(config, endep, 0, itemIds=itemIds, initialize=True)
        
                
        # second data load
        endep = 1739505598 - 600*18
        itemIds = detect_anomalies.run(config, endep, itemIds, detection_stages=detection_stages)

        print(f"Anomalies: {itemIds}")
                

if __name__ == '__main__':
    unittest.main()

    # streamlit run /home/ubuntu/git/pyAnomalyDetector2/tests/test_detector_detect2.py

