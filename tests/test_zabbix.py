import unittest, os
import time

import __init__
import detector
import stats
import check_conn
import viewer
import testlib

class TestZabbix(unittest.TestCase):
    def test_zabbix(self):
        os.environ["SECRET_PATH"] = "/home/minelocal/.creds/zabbix_api.yaml"
        config = "tests/test_zabbix.d/config.yml"
        group_names=["app/cal/sug5k/lab"]
        group_names=None
        #host_names=["lab-sug-mediator03"]
        host_names=None
        max_itemIds = 0
        output = os.path.join(testlib.setup_testdir("test_zabbix"), "result.json")

        self.assertTrue(check_conn.run_check(config))

        stats.update_stats(config, endep=0, group_names=group_names, host_names=host_names, initialize=True, max_itemIds=max_itemIds)

        data = detector.run(config, endep=1737791212, group_names=group_names, max_itemIds=max_itemIds, skip_history_update=True)

        # pretty print json clusters
        import json
        with open(output, 'w') as f:
            json.dump(data, f, indent=4)

        print(data)

        viewer.prepare(config, output)



if __name__ == '__main__':
    unittest.main()