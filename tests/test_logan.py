import unittest, os
import time

import __init__
import detector
import trends_stats
import check_conn
import viewer
import testlib

class TestLogan(unittest.TestCase):
    def test_logan(self):
        config = "tests/test_logan.d/config.yml"
        os.system('cd tests/testdata/loganal && python3 -m http.server 8001 &')
        time.sleep(1)

        endep = int(time.mktime(time.strptime('Fri Mar 21 20:00:00 2025', '%a %b %d %H:%M:%S %Y')))
        output = os.path.join(testlib.setup_testdir("test_logan"), "result")

        itemIds = []
        trends_stats.update_stats(config, endep, 0, initialize=True)


        data = detector.run(config, endep=endep , itemIds=itemIds, 
        skip_history_update=True, trace_mode=True, initialize=True)
        self.assertEqual(len(data), 0)

        os.system('pkill -f http.server')



if __name__ == '__main__':
    unittest.main()