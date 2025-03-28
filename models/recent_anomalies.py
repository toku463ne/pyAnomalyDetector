from typing import List
import pandas as pd

from models.model import Model

class RecentAnomalyModel(Model):
    name = "recent_anomalies"
    sql_template = "recent_anomalies"
    fields = ["itemid", "name", "last_update"]


    def upsert(self, itemid: int, last_update: int):
        # prepare sql
        sql = f"INSERT INTO {self.table_name} (itemid, last_update) VALUES "
        sql += f"({itemid}, {last_update}) "
        sql += " ON CONFLICT (itemid) DO UPDATE SET "
        sql += "last_update = EXCLUDED.last_update;"

        self.db.exec_sql(sql)


    def delete_old_entries(self, oldep: int):
        sql = f"delete from {self.table_name} WHERE last_update < {oldep};"
        self.db.exec_sql(sql)

    
    def filter_itemIds(self, itemIds: List[int], oldep: int):
        sql = f"select itemid from {self.table_name} where last_update >= {oldep} and itemid in (%s);" % ",".join(map(str, itemIds))
        cur = self.db.exec_sql(sql)
        ex_itemIds = []
        for (itemId,) in cur:
            ex_itemIds.append(itemId)
        
        # exclude ex_itemIds from itemIds
        itemIds = [itemId for itemId in itemIds if itemId not in ex_itemIds]

        return itemIds

    def get_all(self) -> pd.DataFrame:
        sql = f"select * from {self.table_name};"
        cur = self.db.exec_sql(sql)
        return pd.DataFrame(cur, columns=self.fields)