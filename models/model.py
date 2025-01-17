
from db.postgresql import PostgreSqlDB
import utils.config_loader as config_loader

class Model:
    name = ""
    sql_template = ""

    def __init__(self, data_source_name=""):
        self.data_source_name = data_source_name
        if data_source_name == "":
            self.table_name = self.name
        else:
            self.table_name = f"{data_source_name}.{self.name}"
        self.db = PostgreSqlDB(config_loader.conf['admdb'])
        self.db.create_table(self.table_name, self.sql_template)

    def truncate(self):
        self.db.exec_sql(f"TRUNCATE TABLE {self.table_name};")
        
    
    