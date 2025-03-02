import unittest, os
import time

import __init__
import detector
import trends_stats
import check_conn
import viewer
import testlib

class TestZabbix(unittest.TestCase):
    def test_zabbix(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config = "tests/test_zabbix2.d/config.yml"
        #group_names=["app/cal/sug5k/lab"]
        group_names=None
        #host_names=["lab-sug-mediator03"]
        host_names=None
        max_itemIds = 0
        output = os.path.join(testlib.setup_testdir("test_zabbix"), "result")

        # self.assertTrue(check_conn.run_check(config))

        endep = 1740787201
        itemIds = [115629]

        trends_stats.update_stats(config, endep=1740848580, itemIds=itemIds, group_names=group_names, host_names=host_names, initialize=True, max_itemIds=max_itemIds)

        data = detector.run(config, endep=1740892561 , itemIds=itemIds, group_names=group_names, max_itemIds=max_itemIds, trace_mode=True, initialize=True)
        for data_source_name, df in data.items():
            if df is None:
                continue
            df.to_csv(f"{output}_{data_source_name}.csv", index=False)
            viewer.prepare(config)



if __name__ == '__main__':
    unittest.main()