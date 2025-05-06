import os
import unittest
import time

import __init__
import utils.config_loader as config_loader
import views.streamlit_view as streamlit_view

class TestStremlit(unittest.TestCase):        
    def test_streamlit(self):
        os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
        config = config_loader.load_config("samples/unified.yml")
        streamlit_view.run(config)


if __name__ == '__main__':
    unittest.main()