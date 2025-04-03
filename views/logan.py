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
        name: "graphycal logs"
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
        self.data_source_name = config['data_source']['name']

    # show charts
    def show(self, data: pd.DataFrame):
        log("show charts")
        if len(data) == 0:
            return
        # get min(itemid) for each group_name, hostid
        data = data.groupby(["group_name", "hostid", "clusterid"]).agg({"itemid": "min"}).reset_index()
        data = data.sort_values(by=["group_name", "hostid"])
        data = data[["group_name", "itemid"]]
        data = data.drop_duplicates(subset=["group_name", "itemid"])

        pagedata = {}
        for _, row in data.iterrows():
            group_name = row["group_name"]
            itemid = row["itemid"]
            if group_name not in pagedata:
                pagedata[group_name] = []
            pagedata[group_name].append(itemid)
        
        # show pagedata in a web page (1 page for each group_name)
        for group_name, itemids in pagedata.items():
            self.show_group(group_name, itemids)

    def show_group(self, group_name, itemids):
        log(f"show group {group_name}")
        if len(itemids) == 0:
            return
        # get data for each itemid
        data = {}
        for itemid in itemids:
            data[itemid] = self.getter.get_data(itemid)
        
        # create a web page for the group
        @self.app.route(f"/{group_name}")
        def show_group_page():
            graphs = []
            for itemid, df in data.items():
                fig = px.line(df, x='time', y='value', title=f'Item {itemid}')
                graphs.append(json.dumps(fig, cls=px.utils.PlotlyJSONEncoder))
            return render_template('group.html', group_name=group_name, graphs=graphs)
        
        self.app.run(debug=True, port=8000)
        log(f"Group {group_name} page is running at http://localhost:8000/{group_name}")
        log("Flask app is running at http://localhost:8000")

        