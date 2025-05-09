import time, os

import __init__
import detect_anomalies
import utils.config_loader as config_loader

os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
config_file="samples/unified.yml"
config = config_loader.load_config(config_file)


detect_anomalies.run(config, time.time()-900)