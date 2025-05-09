import unittest
import time
import os
from decimal import Decimal

import __init__
import trends_stats
from models.models_set import ModelsSet
import data_getter
import trends_stats
import utils.config_loader as config_loader
import update_views

os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
config = config_loader.load_config("samples/zabbix_psql.yml")
data_source_name = "zb10"
update_views.update(config)



