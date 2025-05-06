"""MySQL database connection module."""
import mysql.connector
from mysql.connector import Error
import time
from jinja2 import Template 
import pandas as pd


class MySqlDB:
    def __init__(self, config):
        self.conn = None
        self.config = config
        self.retries = config.get('retries', 1)
        self.delay = config.get('delay', 3)
                
    def connect(self):
        """
        Create a connection to the MySQL database with autocommit enabled.
        """
        if self.conn is not None and self.conn.is_connected():
            return self.conn
        try:
            self.conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                autocommit=True
            )
            if self.conn.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error: {e}")
            time.sleep(self.delay)
            self.retries -= 1
            if self.retries > 0:
                self.connect()
            else:
                raise Exception(f"Failed to connect to MySQL database after {self.config['retries']} retries")
        return self.conn
    
    def exec_sql(self, sql):
        retries = self.retries
        delay = self.delay
        cur = None
        for i in range(retries):
            try:
                cur = self.connect().cursor()
                cur.execute(sql)
                return cur
            except mysql.connector.errors.OperationalError:
                if i < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise  # Give up after max retries
        raise Exception("SQL failed after max tries")
    
    def truncate_table(self, tablename):
        """
        Truncate a table in the MySQL database.
        """
        sql = f"TRUNCATE TABLE {tablename};"
        return self.exec_sql(sql)
    
    def count_table(self, tablename, whereList=[]):
        """
        Count the number of rows in a table.
        """
        if self.table_exists(tablename) == False:
            return 0
        strwhere = ""
        if len(whereList) > 0:
            strwhere = "WHERE %s" % (" AND ".join(whereList))
        sql = f"SELECT COUNT(*) AS cnt FROM {tablename} {strwhere};"
        cur = self.exec_sql(sql)
        res = cur.fetchone()[0]
        cur.close()
        return res


    def close(self):
        if self.conn != None:
            self.conn.close()

    def _create_table_from_template(self, sqlFile, tableName, context={}):
        try:
            with open(sqlFile, "r") as f:
                template = Template(f.read())
            context["TABLENAME"] = tableName
            sql = template.render(context)
            cur = self.exec_sql(sql)
            cur.close()
        except:
            raise

    def create_table(self, tableName, templateName="", replaces={}):
        if templateName != "":
            self._create_table_from_template("%s/postgresql/create_table_%s.sql.j2" % (SQL_DIR, 
                                                        templateName), tableName, replaces)
        else:
            self._create_table_from_template("%s/postgresql/create_table_%s.sql" % (SQL_DIR, 
                                                        tableName), tableName)
    
    def table_exists(self, tableName, schema_name=""):
        """
        Check if a table exists in the MySQL database.
        """
        sql = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{tableName}'"
        if schema_name:
            sql += f" AND table_schema = '{schema_name}'"
        cur = self.exec_sql(sql)
        res = cur.fetchone()[0]
        cur.close()
        return res > 0


    def drop_table(self, tableName):
        self.exec_sql("drop table if exists %s;" % tableName)

    def select1rec(self, sql):
        cur = self.exec_sql(sql)
        row = cur.fetchone()
        cur.close()
        if row:
            return row
        return None

    def select1value(self, tableName, field, whereList=[]):
        sql = "select %s from %s" % (field, tableName)
        if len(whereList) > 0:
            sql += " where %s" % (" and ".join(whereList))
        row = self.select1rec(sql)
        if row:
            (val,) = row
            return val
        return None

    def read_sql(self, sql) -> pd.DataFrame:
        cur = self.exec_sql(sql)
        rows = cur.fetchall()
        cur.close()
        return pd.DataFrame(rows)
    
    
    # create schema if not exists
    def create_schema(self, schema_name):
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        self.exec_sql(sql)
