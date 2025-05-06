"""
class to get data from zabbix postgreSQL database
"""
from data_getter.data_getter import DataGetter
from typing import Dict, List
import pandas as pd # type: ignore

from db.mysql import MySqlDB

class ZabbixMySqlGetter(DataGetter):
    history_tables = ['history', 'history_uint']
    trends_tables = ['trends', 'trends_uint']
    fields = ['itemid', 'clock', 'value']
    fields_full = ['itemid', 'clock', 'value_min', 'value_avg', 'value_max']
    db: MySqlDB = None

    def init_data_source(self, data_source: Dict):
        self.db = MySqlDB(data_source)
        self.hstgrp_table = 'hstgrp'
        version = self.db.select1value("dbversion", "mandatory")
        if str(version)[0] == "3":
            self.hstgrp_table = 'groups'
        self.api_url = data_source['api_url']

    def check_conn(self) -> bool:
        cur = self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        cur = self.db.exec_sql("SELECT VERSION();")
        cnt = 0
        for row in cur:
            cnt += 1
        return cnt > 0

    def get_history_data(self, startep: int, endep: int, itemIds: List[int] = [], use_cache=False) -> pd.DataFrame:
        if len(itemIds) > 0:
            where_itemIds = " AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT itemid, clock, value
            FROM history
            WHERE clock BETWEEN {startep} AND {endep}
            {where_itemIds}
            UNION ALL
            SELECT itemid, clock, value
            FROM history_uint
            WHERE clock BETWEEN {startep} AND {endep}
            {where_itemIds}
        """

        # Split and execute SET and SELECT separately
        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        df = self.db.read_sql(sql.split(';', 1)[1])
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields, dtype=object)
        df.columns = self.fields
        df = df.sort_values(['itemid', 'clock'])
        return df

    def get_trends_data(self, startep: int, endep: int, itemIds: List[int] = [], use_cache=False) -> pd.DataFrame:
        if len(itemIds) > 0:
            where_itemIds = " AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT itemid, clock, value_avg as value
            FROM trends
            WHERE clock BETWEEN {startep} AND {endep}
            {where_itemIds}
            UNION ALL
            SELECT itemid, clock, value_avg as value
            FROM trends_uint
            WHERE clock BETWEEN {startep} AND {endep}
            {where_itemIds}
        """

        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        df = self.db.read_sql(sql.split(';', 1)[1])
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields, dtype=object)
        df.columns = self.fields
        df = df.sort_values(['itemid', 'clock'])
        return df

    def get_trends_full_data(self, startep: int, endep: int, itemIds: List[int] = [], use_cache=False) -> pd.DataFrame:
        if len(itemIds) > 0:
            where_itemIds = " AND itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT itemid, clock, value_min, value_avg, value_max
            FROM trends
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
            UNION ALL
            SELECT itemid, clock, value_min, value_avg, value_max
            FROM trends_uint
            WHERE clock >= {startep} AND clock <= {endep}
            {where_itemIds}
        """

        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        df = self.db.read_sql(sql.split(';', 1)[1])
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields_full, dtype=object)
        df.columns = self.fields_full
        df = df.sort_values(['itemid', 'clock'])
        return df

    def get_itemIds(self, item_names: List[str] = [], 
                    host_names: List[str] = [], 
                    group_names: List[str] = [],
                    itemIds: List[int] = [],
                    max_itemIds = 0) -> List[int]:
        where_conds = []
        names_list = [("items", item_names), ("hosts", host_names), (self.hstgrp_table, group_names)]
        for (table_name, names) in names_list:
            if len(names) > 0:
                name_conds = []
                for name in names:
                    if '*' in name or '%' in name:
                        name_conds.append(f"{table_name}.name LIKE '{name.replace('*', '%')}'")
                    else:
                        name_conds.append(f"{table_name}.name = '{name}' OR {table_name}.name LIKE '{name}/%'")
                where_conds.append("(" + " OR ".join(name_conds) + ")")

        if len(itemIds) > 0:
            where_conds.append(" items.itemid IN (%s)" % ",".join(map(str, itemIds)))

        if where_conds:
            where_itemIds = "WHERE " + " AND ".join(where_conds)
        else:
            where_itemIds = ""

        limitcond = ""
        if max_itemIds > 0:
            limitcond = f" LIMIT {max_itemIds}"
        
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT items.itemid
            FROM hosts 
            INNER JOIN items ON hosts.hostid = items.hostid
            INNER JOIN hosts_groups ON hosts_groups.hostid = hosts.hostid
            INNER JOIN {self.hstgrp_table} ON {self.hstgrp_table}.groupid = hosts_groups.groupid 
            {where_itemIds}
            {limitcond}
        """

        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        cur = self.db.exec_sql(sql.split(';', 1)[1])
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
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT itemid, hostid
            FROM items
            {where_itemIds}
        """

        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        cur = self.db.exec_sql(sql.split(';', 1)[1])
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return {}
        return {row[0]: row[1] for row in rows}

    def classify_by_groups(self, itemIds: List[int], group_names: List[str]) -> Dict[str, List[int]]:
        if len(group_names) == 0:
            return {"all": itemIds}
        if len(itemIds) == 0:
            return {"all": []}
        cond_itemIds = "AND items.itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        groups = {}
        for group_name in group_names:
            sql = f"""
                SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
                SELECT DISTINCT items.itemid
                FROM items 
                INNER JOIN hosts ON hosts.hostid = items.hostid
                INNER JOIN hosts_groups ON hosts_groups.hostid = hosts.hostid
                INNER JOIN {self.hstgrp_table} ON {self.hstgrp_table}.groupid = hosts_groups.groupid 
                WHERE ({self.hstgrp_table}.name = '{group_name}' OR {self.hstgrp_table}.name LIKE '{group_name}/%') 
                {cond_itemIds}
            """
            self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
            cur = self.db.exec_sql(sql.split(';', 1)[1])
            rows = cur.fetchall()
            cur.close()
            if len(rows) == 0:
                continue
            group_info = [row[0] for row in rows]
            if len(group_info) > 0: 
                groups[group_name] = group_info
        return groups

    def get_item_relations(self, itemIds: List[int], group_names: List[str]) -> pd.DataFrame:
        df = pd.DataFrame()
        if len(itemIds) > 0:
            where_itemIds = "AND items.itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        else:
            where_itemIds = ""
        for name in group_names:
            if '*' in name or '%' in name:
                where_cond = f"{self.hstgrp_table}.name LIKE '{name.replace('*', '%')}'"
            else:
                where_cond = f"{self.hstgrp_table}.name = '{name}' OR {self.hstgrp_table}.name LIKE '{name}/%'"
            sql = f"""SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
                SELECT '{name}' AS group_name, hosts.hostid, items.itemid
                FROM hosts 
                INNER JOIN items ON hosts.hostid = items.hostid
                INNER JOIN hosts_groups ON hosts_groups.hostid = hosts.hostid
                INNER JOIN {self.hstgrp_table} ON {self.hstgrp_table}.groupid = hosts_groups.groupid 
                WHERE {where_cond}
                {where_itemIds}
            """
            self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
            df = pd.concat([df, self.db.read_sql(sql.split(';', 1)[1])], ignore_index=True)
        numeric_cols = df.select_dtypes(include=['float']).columns
        df[numeric_cols] = df[numeric_cols].astype(int)
        df.columns = ['group_name', 'hostid', 'itemid']
        return df

    def get_item_details(self, itemIds: List[int]) -> Dict:
        if len(itemIds) == 0:
            return {}
        where_itemIds = "WHERE items.itemid IN (" + ",".join([str(itemid) for itemid in itemIds]) + ")"
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT items.itemid, hosts.hostid, hosts.name AS host_name, items.name AS item_name
            FROM items 
            INNER JOIN hosts ON hosts.hostid = items.hostid
            {where_itemIds}
        """
        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        cur = self.db.exec_sql(sql.split(';', 1)[1])
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return {}
        return {row[0]: {"hostid": row[1], "host_name": row[2], "item_name": row[3]} for row in rows}

    def check_itemId_cond(self, itemIds: List[int], item_cond: str) -> bool:
        if item_cond == "":
            return itemIds
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT itemid
            FROM items
            WHERE itemid IN ({",".join(map(str, itemIds))}) AND {item_cond}
        """
        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        cur = self.db.exec_sql(sql.split(';', 1)[1])
        rows = cur.fetchall()
        cur.close()
        return [row[0] for row in rows]

    def get_items_details(self, itemIds: List[int]) -> pd.DataFrame:
        sql = f"""
            SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
            SELECT {self.hstgrp_table}.name AS group_name, hosts.hostid AS hostid, hosts.host AS host_name, items.itemid AS itemid, items.key_ AS item_name
            FROM hosts 
            INNER JOIN items ON hosts.hostid = items.hostid
            INNER JOIN hosts_groups ON hosts_groups.hostid = hosts.hostid
            INNER JOIN {self.hstgrp_table} ON {self.hstgrp_table}.groupid = hosts_groups.groupid 
            WHERE items.itemid IN ({",".join(map(str, itemIds))})
        """
        self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        df = self.db.read_sql(sql.split(';', 1)[1])
        df.columns = ['group_name', 'hostid', 'host_name', 'itemid', 'item_name']
        return df

    def get_group_map(self, itemIds: List[int], group_names: List[str]) -> Dict[int, str]:
        if len(itemIds) == 0 or len(group_names) == 0:
            return {}
        group_map = {}
        for group_name in group_names:
            sql = f"""
                SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
                SELECT items.itemid
                FROM hosts 
                INNER JOIN items ON hosts.hostid = items.hostid
                INNER JOIN hosts_groups ON hosts_groups.hostid = hosts.hostid
                INNER JOIN {self.hstgrp_table} ON {self.hstgrp_table}.groupid = hosts_groups.groupid 
                WHERE ({self.hstgrp_table}.name = '{group_name}' OR {self.hstgrp_table}.name LIKE '{group_name}/%') 
                AND items.itemid IN ({",".join(map(str, itemIds))})
            """
            self.db.exec_sql("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
            cur = self.db.exec_sql(sql.split(';', 1)[1])
            rows = cur.fetchall()
            cur.close()
            if len(rows) == 0:
                continue
            for row in rows:
                group_map[row[0]] = group_name
        return group_map

    def get_item_html_title(self, itemId: int, chart_type="") -> str:
        detail = self.get_item_details([itemId]).get(itemId, {"host_name": "", "item_name": ""})
        href = f"{self.api_url}/history.php?itemids%5B0%5D={itemId}&period=now-730h"
        if chart_type == "topitems":
            href += f"&chart_type={chart_type}"
        return f"""<a href="{href}" target="_blank">
        {detail["host_name"][:50]}<br>
        {detail["item_name"][:50]}<br>
        {itemId}</a>"""


    def get_itemId_by_cond(self, cond, limit=0) -> List[int]:
        sql = f"SELECT itemid FROM items WHERE {cond}"
        if limit > 0:
            sql += f" limit {limit}"

        cur = self.db.exec_sql(sql)
        rows = cur.fetchall()
        cur.close()
        
        return [row[0] for row in rows]