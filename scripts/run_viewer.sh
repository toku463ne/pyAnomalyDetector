#!/bin/bash
# time scripts/run_viewer.sh -c tests/test_zabbix.d/config.yml --data /tmp/anom.json
source scripts/venv/bin/activate
export SECRET_PATH="/home/minelocal/.creds/zabbix_api.yaml"
python3 viewer.py $@