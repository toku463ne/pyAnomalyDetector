import os
import unittest
import time

import __init__
import utils.config_loader as config_loader
import update_topitems

class TestStremlit(unittest.TestCase):        
    def test_streamlit(self):
        os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
        config = config_loader.load_config("samples/logan.yml")
        update_topitems.run(config)

        update_topitems.classify_charts(time.time()-900)


if __name__ == '__main__':
    unittest.main()