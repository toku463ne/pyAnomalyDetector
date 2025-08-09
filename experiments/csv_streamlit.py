import os, time
import __init__
import utils.config_loader as config_loader
import views.streamlit_view as streamlit_view
from models.models_set import ModelsSet

# source $HOME/venv/bin/activate
# streamlit run /data/git/pyAnomalyDetector/experiments/csv_streamlit.py

conf = config_loader.conf

name = 'test_csv'
data_source = {
            'type': 'csv',
            'data_dir': 'testdata/csv/20250518'
        }


conf['data_sources'] = {}
conf['data_sources'][name] = data_source
config_loader.cascade_config("data_sources")

view_source ={
    "type": "streamlit",
    "port": 5201,
    "n_sigma": 3,
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

conf['view_sources'] = {"test_csv": view_source}
config_loader.cascade_config("view_sources")

ms = ModelsSet(name)
ms.anomalies.import_data(os.path.join(data_source['data_dir'], 'anomalies.csv.gz'))

endep = 1747536901

streamlit_view.run(conf)
