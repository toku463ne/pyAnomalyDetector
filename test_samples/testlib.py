import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils.config_loader as config_loader

def load_config(config_file):
    os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
    config_loader.load_config(config_file)
    config = config_loader.conf
    config["admdb"]["dbname"] = "anomdec_test"
    return config


    

        

