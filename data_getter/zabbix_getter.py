"""
class to get data from zabbix postgreSQL database
"""
from data_getter.data_getter import DataGetter
from typing import Dict, List
import pandas as pd # type: ignore

from db.postgresql import PostgreSqlDB

class ZabbixGetter(DataGetter):
    history_tables = ['history', 'history_uint']
    trends_tables = ['trends', 'trends_uint']
    fields = ['itemid', 'clock', 'value']
    db: PostgreSqlDB = None

    def init_data_source(self, data_source: Dict):
        self.db = PostgreSqlDB(data_source)


    def get_history_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        if len(itemIds) > 0:
            where_itemIds = " AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        # join history and history_uint tables
        sql = f"""
            SELECT itemid, clock, value
            FROM history
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
            UNION
            SELECT itemid, clock, value
            FROM history_uint
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
        """

        df = self.db.read_sql(sql)
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields)
        df.columns = self.fields
        return df
    

    def get_trends_data(self, startep: int, endep: int, itemIds: List[int] = []) -> pd.DataFrame:
        if len(itemIds) > 0:
            where_itemIds = " AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        # join trends and trends_uint tables
        sql = f"""
            SELECT itemid, clock, value_avg as value
            FROM trends
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
            UNION
            SELECT itemid, clock, value_avg as value
            FROM trends_uint
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
        """

        df = self.db.read_sql(sql)
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields)
        df.columns = self.fields
        return df
    

    def get_itemIds(self, item_names: list[str] = [], 
                    host_names: list[str] = [], 
                    group_names: list[str] = []) -> List[int]:
        where_conds = []
        # if names includes '*', convert them to '%' and use LIKE operator
        # else use '=' operator
        names_list = [item_names, host_names, group_names]
        for names in names_list:
            if len(names) > 0:
                name_conds = []
                for name in names:
                    if '*' in name or '%' in name:
                        name_conds.append(f"name LIKE '{name.replace('*', '%')}'")
                    else:
                        name_conds.append(f"name = '{name}'")
                where_conds.append("(" + " OR ".join(name_conds) + ")")

        if where_conds:
            where_itemIds = "WHERE " + " AND ".join(where_conds)
        else:
            where_itemIds = ""
        
        sql = f"""
            SELECT itemid
            FROM items
            {where_itemIds}
        """

        cur = self.db.exec_sql(sql)
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return []
        return [row[0] for row in rows]
    

    def get_item_host_dict(self, itemIds: List[int] = []) -> Dict[int, int]:
        if len(itemIds) > 0:
            where_itemIds = "WHERE itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        sql = f"""
            SELECT itemid, hostid
            FROM items
            {where_itemIds}
        """

        cur = self.db.exec_sql(sql)
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return {}
        return {row[0]: row[1] for row in rows}
    

    def classify_by_groups(self, itemIds: List[int], group_names: List[str]) -> Dict[str, List[int]]:
        if len(group_names) == 0:
            return {"all": itemIds}
        
        if len(itemIds) > 0:
            cond_itemIds = "AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            cond_itemIds = ""

        
        # get groupid from given group_names considering sub groups.
        # ex) app/sim/rp is sub group of app/sim
        groups = {}
        for group_name in group_names:
            sql = f"""
                SELECT i.itemid
                FROM items i
                JOIN hosts h ON i.hostid = h.hostid
                JOIN hosts_groups hg ON h.hostid = hg.hostid
                WHERE g.name = '{group_name}' OR g.name LIKE '{group_name}/%'
                {cond_itemIds}
            """

            cur = self.db.exec_sql(sql)
            rows = cur.fetchall()
            cur.close()
            if len(rows) == 0:
                continue

            group_info = [row[0] for row in rows]
            if len(group_info) > 0: 
                groups[group_name] = group_info

        return groups
            