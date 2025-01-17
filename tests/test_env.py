"""
unit tests for env.py
"""
import unittest, os

import __init__
import tests.testlib as testlib
import utils.config_loader as config_loader

class TestEnv(unittest.TestCase):
    # test load_config
    def test_env(self):
        datadir = "tests/test_env.d"
        testdir = testlib.setup_testdir("test_env")
        os.environ['LOG_DIR'] = testdir

        config_loader.load_config(os.path.join(datadir, 'config.yml'))
        conf = config_loader.conf
        self.assertIsNotNone(conf)
        
        ds0 = conf['data_sources'][0]
        self.assertEqual(ds0['name'], 'zabbix')
        self.assertEqual(ds0['password'], 'zabbix_pass')

        self.assertEqual(conf['logging']['file'], os.path.join(testdir, 'anomdec.log'))


if __name__ == '__main__':
    unittest.main()