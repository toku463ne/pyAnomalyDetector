import os
import yaml
from jinja2 import Template
import logging

SECRET_PATH = 'SECRET_PATH'
LOG_DIR = 'LOG_DIR'
DEFAULT_BATCH_SIZE = 1000

BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
SQL_DIR = os.path.join(BASE_DIR, "db/sql")

conf = {}

def load_config(config_path=None, additional_context={}):
    global conf
    global log_file

    with open('config/default.yml', 'r') as file:
        conf = yaml.safe_load(file)

    if config_path:
        with open(config_path, 'r') as file:
            override_config = yaml.safe_load(file)
        for key, value in override_config.items():
            if isinstance(value, dict) and key in conf:
                conf[key].update(value)
            else:
                conf[key] = value

    # if os env var SECRET_PATH is set, use that
    if SECRET_PATH in os.environ:
        secret_path = os.environ[SECRET_PATH]
    else:
        secret_path = conf.get('secret_path', None)
        secrets = {}

    if secret_path:
        with open(secret_path, 'r') as file:
            secrets = yaml.safe_load(file)
    
    # os environment variables
    context = {}
    for k in os.environ:
        context[k] = os.environ[k]

    # default log directory
    if LOG_DIR not in context:
        context[LOG_DIR] = "/tmp"

    context.update(secrets)
    context.update(additional_context)

    conf = yaml.safe_load(Template(yaml.dump(conf)).render(context))

    conf['batch_size'] = conf.get('batch_size', DEFAULT_BATCH_SIZE)

    l = conf.get("logging", None)
    if l:
        # setup logging
        logging.basicConfig(
            filename=l.get("file", "anomdec.log"),
            level=getattr(logging, l.get("level", "INFO").upper(), logging.INFO),
            format=l.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )




