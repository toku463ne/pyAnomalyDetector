import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
import utils.config_loader as config_loader
config_loader.load_config(os.path.join('experiments', 'config.yml'))