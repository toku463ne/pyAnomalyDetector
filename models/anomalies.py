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
    fields = ["group_name", "itemid", "hostid", "host_name", "item_name"]

    def get_data(self, where_conds: List[str] = []) -> pd.DataFrame:
        sql = f"SELECT * FROM {self.table_name}"
        if len(where_conds) > 0:
            sql += " WHERE " + " AND ".join(where_conds)
        
        df = self.db.read_sql(sql)
        if df.empty:
            return pd.DataFrame(columns=self.fields, dtype=object)
        df.columns = self.fields
        return df
    
    
    def import_data(self, data: pd.DataFrame):
        self.truncate()

        for _, row in data.iterrows():
            sql = f"""INSERT INTO {self.table_name} 
(group_name, itemid, hostid, host_name, item_name) 
VALUES 
('{row.group_name}', {row.itemid}, {row.hostid}, '{row.host_name}', '{row.item_name}');"""
            self.db.exec_sql(sql)

