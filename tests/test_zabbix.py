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
        #group_names=["app/cal/sug5k/lab"]
        group_names=None
        #host_names=["lab-sug-mediator03"]
        host_names=None
        max_itemIds = 0
        output = os.path.join(testlib.setup_testdir("test_zabbix"), "result")

        # self.assertTrue(check_conn.run_check(config))

        #stats.update_stats(config, endep=0, group_names=group_names, host_names=host_names, initialize=True, max_itemIds=max_itemIds)

        itemIds = [23328, 51782, 54832, 58616, 58691, 58705, 77985, 78293, 78294, 79482, 79690, 80568, 
        80596, 81294, 81427, 81452, 81733, 82503, 83046, 83434, 83538, 86009, 86018, 86320, 86367, 87969, 
        93474, 93749, 96409, 97788, 98823, 98825, 98880, 98881, 107271, 107957, 108701, 108746, 111635, 
        111868, 111879, 111884, 111896, 111993, 112119, 112144, 125196, 129396, 132126, 138564, 141501, 
        199731, 210960, 210998, 210999, 215713, 221896, 223909, 223913, 223914, 226231, 226656, 226661, 
        228214, 229297, 229900, 231160, 233842, 235424, 241246, 241250, 241590, 241609, 242391, 242397, 
        242405, 254060, 255214, 255260, 257477, 257479, 258153, 258165, 258166, 258167, 258645, 258646, 
        258650, 260762, 264126, 264964, 266443, 268130, 268131, 270122, 270661, 329759, 331659, 342063, 345681]


        data = detector.run(config, endep=1738478400 , itemIds=itemIds, group_names=group_names, max_itemIds=max_itemIds, skip_history_update=False)
        for data_source_name, df in data.items():
            if df is None:
                continue
            df.to_csv(f"{output}_{data_source_name}.csv", index=False)
            viewer.prepare(config, output)



if __name__ == '__main__':
    unittest.main()