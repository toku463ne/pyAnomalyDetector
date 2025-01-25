"""
unit tests for zabbix_dashboard.py
"""
import unittest

import __init__
import views



class TestZabbixDashboard(unittest.TestCase):  
    def test_zabbix_dashboard(self):
        view_source = {
            'name': 'zabbix',
            'type': 'zabbix_dashboard',
            'api_url': 'http://localhost/zabbix',
            'user': 'Admin',
            'password': 'zabbix'
        }

        data = {
            'groups': {
                'group1': [10061, 10062, 10062],
                'group2': [22183, 22185, 22187]
            }
        }
        
        v = views.get_view(view_source)
        self.assertIsNotNone(v)

        v.delete_dashboard('test_zabbix_dashboard')

        v.show('test_zabbix_dashboard', data)

        d = v.get_dashboard('test_zabbix_dashboard')
        self.assertIsNotNone(d)
        

        
if __name__ == '__main__':
    unittest.main()