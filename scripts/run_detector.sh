#!/bin/bash
# time scripts/run_detector.sh -c tests/test_zabbix.d/config.yml --output /tmp/anom.json --skip-history-update --end 1737791212
source scripts/venv/bin/activate
export SECRET_PATH="/home/minelocal/.creds/zabbix_api.yaml"
python3 detector.py $@