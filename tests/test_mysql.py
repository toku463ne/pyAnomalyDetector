import __init__
import unittest

import db.mysql as my
import tests.testlib as testlib

class TestMySQL(unittest.TestCase):
    def test_mysql(self):
        testlib.load_test_conf()
        data_source = {
            "type": "mysql",
            "host": "localhost",
            "user": "anomdec",
            "password": "anomdec_pass",
            "database": "anomdec_test"
        }
        db = my.MySqlDB(data_source)

        sql = "drop table if exists test_table1;"
        db.exec_sql(sql)

        sql = "create table if not exists test_table1 (id int, name varchar(10));"
        db.exec_sql(sql)

        db.truncate_table("test_table1")

        sql = "insert into test_table1 values(1, 'test1');"
        db.exec_sql(sql)

        cnt = db.count_table("test_table1")
        self.assertEqual(cnt, 1)

        sql = "drop table if exists test_table1;"
        db.exec_sql(sql)



if __name__ == "__main__":
    unittest.main()