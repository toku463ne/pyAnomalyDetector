#!/bin/bash
# time scripts/run_viewer.sh -c tests/test_zabbix.d/config.yml
source $HOME/venv/bin/activate
export SECRET_PATH="$HOME/.creds/zabbix_api.yaml"
python3 viewer.py $@