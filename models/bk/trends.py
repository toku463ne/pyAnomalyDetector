import pandas as pd

from models.model import Model

class TrendsModel(Model):
    """ fields:
        itemid INTEGER PRIMARY KEY,
        clock INTEGER,
        value FLOAT
    """
    sql_template = "history"
    name = "trends"
    fields = ['itemid', 'clock', 'value']

    def get_data(self, itemIds: list[int]=[], startep: int = 0, endep: int = 0) -> pd.DataFrame:
        sql = f"SELECT * FROM {self.table_name}"
        where = []
        if len(itemIds) > 0:
            where.append(f"itemid IN ({','.join(map(str, itemIds))})")
        if startep > 0:
            where.append(f"clock >= {startep}")
        if endep > 0:
            where.append(f"clock <= {endep}")
        if len(where) > 0:
            sql += " WHERE " + " AND ".join(where)
        
        return self.db.read_sql(sql)


    def insert(self, itemids: list[int], clocks: list[int], values: list[float]):
        # prepare sql
        sql = f"INSERT INTO {self.table_name} (itemid, clock, value) VALUES "
        for i in range(len(itemids)):
            sql += f"({itemids[i]}, {clocks[i]}, {values[i]}),"
        sql = sql[:-1] + ";"

        self.db.exec_sql(sql)
        
    def remove_old_data(self, clock: int):
        sql = f"DELETE FROM {self.table_name} WHERE clock < {clock};"
        self.db.exec_sql(sql)        
        

    