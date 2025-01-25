#!/bin/bash
# time scripts/run_stats.sh -c tests/test_zabbix.d/config.yml --init
source scripts/venv/bin/activate
export SECRET_PATH="/home/minelocal/.creds/zabbix_api.yaml"
python3 stats.py $@