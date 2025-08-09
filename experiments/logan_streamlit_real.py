import os, time
import __init__
import utils.config_loader as config_loader
import views.streamlit_view as streamlit_view
import update_topitems
import trends_stats
from models.models_set import ModelsSet
import data_getter

# streamlit run /home/ubuntu/git/pyAnomalyDetector2/experiments/logan_streamlit.py

conf = config_loader.conf
name = 'logan_rp'
data_source = {
    'name': name,
    'base_url': 'http://localhost:8101/',
    'data_dir': '/tmp/anomdec_test',
    'type': 'logan',
    'top_n': 10,
    'groups': {
        'proxy': {
            6: {
            'base_url': 'http://192.168.88.170:9501',
            'name': 'common-prod-nfrp170',
            'minimal_group_size': 10000}
        }
    }
}


conf['data_sources'] = {}
conf['data_sources'][name] = data_source
config_loader.cascade_config("data_sources")

view_source ={
    "type": "streamlit",
    "port": 5200,
    "n_sigma": 2,
    "chart_categories": {
        "bycluster": {
            "name": "By Cluster",
            "one_item_per_host": False
        },
        "bygroup": {
            "name": "By Group",
            "one_item_per_host": False
        }
    },
    "layout": {
        "chart_width": 400,
        "chart_height": 300,
        "max_vertical_charts": 4,
        "max_horizontal_charts": 3
    } 
}

conf['view_sources'] = {"test_logan": view_source}
config_loader.cascade_config("view_sources")

endep = 0
trends_stats.update_stats(conf, endep=0)

update_topitems.run(conf, endep=endep)

ms = ModelsSet(name)
itemIds = ms.topitems.get_itemids()
dg = data_getter.get_data_getter(data_source)


d = dg.get_item_html_title(6174196468300004)
print(d)


streamlit_view.run(conf)
