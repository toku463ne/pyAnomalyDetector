from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import json

from views.view import View
import data_getter
import logging

def log(msg, level=logging.INFO):
    msg = f"[views/localweb.py] {msg}"
    logging.log(level, msg)


"""
view_sources:
  "localweb":
    type: "localweb"
    url: "http://localhost:8000"
    user: "admin"
    password: "zabbix
    data_source: 
        name: "localweb"
        type: "logan"
        base_url: "http://localhost:8001/logan"
        group_names:
            group1:
                host_names:
                    - host1
                    - host2
            group2:
                host_names:
                    - host3
                    - host4
"""

class LocalWeb(View):
    def __init__(self, config):
        self.app = Flask(__name__)
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        self.getter = data_getter.get_data_getter(config['data_source'])

    

