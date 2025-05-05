import unittest, os

import __init__
import tests.testlib as testlib
import utils.config_loader as config_loader

class TestConfigLoader(unittest.TestCase):
    # test load_config
    def test_env(self):
        os.environ['ANOMDEC_SECRET_PATH'] = os.path.join('tests', 'test_secret.yml')

        conf = config_loader.load_config()
        self.assertIsNotNone(conf)
        self.assertIn('logging', conf)

        l = conf["logging"]
        self.assertEqual(l["log_dir"], os.path.join(os.environ["HOME"], "anomdec/logs"))

        admdb = conf["admdb"]
        self.assertEqual(admdb["host"], "localhost")
        self.assertEqual(admdb["user"], "anomdec")
        self.assertEqual(admdb["password"], "anomdec_pass")


    def test_env_with_datasource(self):
        os.environ['ANOMDEC_SECRET_PATH'] = os.path.join('tests', 'test_secret.yml')

        conf = config_loader.load_config("testdata/yaml/config_with_datasource.yml")
        self.assertIsNotNone(conf)
        self.assertIn('logging', conf)
        self.assertIn('data_sources', conf)

        data_source = conf["data_sources"]["logan"]
        self.assertEqual(data_source["trends_interval"], 7200) # cascaded value
        self.assertEqual(data_source["history_interval"], 600) # default value

        self.assertNotIn("logging", data_source)
        self.assertNotIn("admdb", data_source)
        self.assertNotIn("data_sources", data_source)

        
if __name__ == '__main__':
    unittest.main()
