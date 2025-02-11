#!/bin/bash
# time scripts/run_detector.sh -c tests/test_zabbix.d/config.yml --skip-history-update --end 1737791212
source $HOME/venv/bin/activate
export SECRET_PATH="$HOME/.creds/zabbix_api.yaml"
python3 detector.py $@
