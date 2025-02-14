import pandas as pd
from typing import List

from models.model import Model

class AnomaliesModel(Model):
    """ fields:
            group_name STRING,
            groupid INTEGER,
            itemid INTEGER,
            hostid INTEGER,
            host_name STRING,
            item_name STRING,
    """
    sql_template = "anomalies"
    name = sql_template
    fields = ["itemid", "created", "group_name", "hostid", "clusterid", "host_name", "item_name"]

    def get_data(self, where_conds: List[str] = []) -> pd.DataFrame:
        sql = f"SELECT * FROM {self.table_name}"
        if len(where_conds) > 0:
            sql += " WHERE " + " AND ".join(where_conds)
        
        df = self.db.read_sql(sql)
        if df.empty:
            return pd.DataFrame(columns=self.fields, dtype=object)
        df.columns = self.fields
        return df
    
    
    def insert_data(self, data: pd.DataFrame):
        for _, row in data.iterrows():
            sql = f"""INSERT INTO {self.table_name} 
    (itemid, created, hostid, clusterid, group_name, host_name, item_name) 
    VALUES 
    ({row.itemid}, {row.created}, 
     {row.hostid}, {row.clusterid}, 
     '{row.group_name}', '{row.host_name}', '{row.item_name}')"""
            self.db.exec_sql(sql)


    def delete_old_entries(self, oldep: int):
        sql = f"delete from {self.table_name} WHERE created < {oldep};"
        self.db.exec_sql(sql)

    
    def filter_itemIds(self, itemIds: List[int], created: int):
        sql = f"select itemid from {self.table_name} where created >= {created} and itemid in (%s);" % ",".join(map(str, itemIds))
        cur = self.db.exec_sql(sql)
        ex_itemIds = []
        for (itemId,) in cur:
            ex_itemIds.append(itemId)
        
        # exclude ex_itemIds from itemIds
        itemIds = [itemId for itemId in itemIds if itemId not in ex_itemIds]

        return itemIds

    