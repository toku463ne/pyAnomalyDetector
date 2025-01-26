#!/bin/bash
# time scripts/get_zabbix_data.sh -c tests/test_zabbix.d/config.yml --end 1737791212 --itemsfile /data/testing/anom/001/items.txt --outdir /data/testing/anom/001 
source scripts/venv/bin/activate
export SECRET_PATH="$HOME/.creds/zabbix_api.yaml"

python3 tools/zabbix.py $@