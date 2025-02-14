#!/bin/bash
# time scripts/get_zabbix_data.sh -c tests/test_zabbix.d/config.yml --end 1744840800 --itemsfile /data/testing/anom/004/items.txt --groupsfile /data/testing/anom/004/groups.txt --outdir /data/testing/anom/004 
source $HOME/venv/bin/activate
export SECRET_PATH="$HOME/.creds/zabbix_api.yaml"

python3 tools/zabbix.py $@