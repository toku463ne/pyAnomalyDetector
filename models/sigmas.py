import pandas as pd
from typing import List

from models.model import Model

class SigmasModel(Model):
    """ fields:
        itemid: INT
        clock: INT
        mean: FLOAT
        s1: FLOAT
        s2: FLOAT
        s3: FLOAT
    """
    sql_template = "sigmas"
    name = sql_template
    fields = ['itemid', 'clock', 'mean1', 'mean2', 's1', 's2', 's3']


    
    def upsert_stds(self, itemid: int, clock: int, mean: float, s1: float, s2: float, s3: float):
        # prepare sql
        sql = f"INSERT INTO {self.table_name} (itemid, clock, mean, s1, s2, s3) VALUES "
        sql += f"({itemid}, {clock}, {mean}, {s1}, {s2}, {s3}) "
        sql += " ON CONFLICT (itemid) DO UPDATE SET "
        sql += "clock = EXCLUDED.clock, mean = EXCLUDED.mean, s1 = EXCLUDED.s1, "
        sql += "s2 = EXCLUDED.s2, "
        sql += "s3 = EXCLUDED.s3;"
        sql = sql[:-1] + ";"

        self.db.exec_sql(sql)
        
    def read_stds(self, itemids: List[int] = []) -> pd.DataFrame:
        sql = f"SELECT * FROM {self.table_name}"
        where = []
        if len(itemids) > 0:
            where.append(f"itemid IN ({','.join(map(str, itemids))})")
        if len(where) > 0:
            sql += " WHERE " + " AND ".join(where)

        df = self.db.read_sql(sql)
        if len(df) == 0:
            return pd.DataFrame(columns=self.fields, dtype=object)
        df.columns = self.fields
        return df

    