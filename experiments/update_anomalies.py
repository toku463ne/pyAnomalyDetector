import unittest
import time
import os
from decimal import Decimal

import __init__
import trends_stats
from models.models_set import ModelsSet
import data_getter
import trends_stats
from data_processing.detector import Detector
import utils.config_loader as config_loader

os.environ['ANOMDEC_SECRET_PATH'] = os.path.join(os.environ['HOME'], '.creds/anomdec.yaml')
config = config_loader.load_config("samples/unified.yml")
data_source_name = "zb10"
d = Detector(data_source_name, config["data_sources"][data_source_name])

d.update_anomalies(1746521701, [Decimal('266920.0'), Decimal('266919.0')])




