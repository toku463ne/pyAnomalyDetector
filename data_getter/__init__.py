def get_data_getter(data_source_config):
    if data_source_config['type'] == 'csv':
        from data_getter.csv_getter import CsvGetter
        return CsvGetter(data_source_config)
    if data_source_config['type'] == 'zabbix_psql':
        from data_getter.zabbix_psql_getter import ZabbixPSqlGetter
        return ZabbixPSqlGetter(data_source_config)
    if data_source_config['type'] == 'zabbix_mysql':
        from data_getter.zabbix_mysql_getter import ZabbixMySqlGetter
        return ZabbixMySqlGetter(data_source_config)
    if data_source_config['type'] == 'logan':
        from data_getter.logan_getter import LoganGetter
        return LoganGetter(data_source_config)
    