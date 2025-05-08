import os, time
import __init__
import utils.config_loader as config_loader
import views.streamlit_view as streamlit_view
import update_topitems

# streamlit run /home/ubuntu/git/pyAnomalyDetector2/experiments/logan_streamlit.py

conf = config_loader.conf

name = 'test_logan'
data_source = {
    'base_url': 'http://localhost:8101/',
    'data_dir': '/tmp/anomdec_test',
    'name': name,
    'type': 'logan',
    'top_n': 10,
    'groups': {
        'proxy': {
            1: 'proxy01',
            2: 'proxy02'
        },
        'firewall': {
            3: 'fw01',
            4: 'fw02',
        },
    },
    'minimal_group_size': 1000
}
os.system('cd testdata/loganal && python3 -m http.server 8101 &')
time.sleep(1)


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

endep = 1746108000
update_topitems.run(conf, endep=endep)

streamlit_view.run(conf)
