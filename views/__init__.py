
def get_view(view_config):
    if view_config['type'] == 'zabbix_dashboard':
        from views.zabbix import ZabbixDashboard
        return ZabbixDashboard(view_config)
    else:
        return None