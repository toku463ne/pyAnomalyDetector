#!/bin/bash
# time scripts/run_viewer.sh -c samples/zabbix.yml 

if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi

echo "$(date) uv run python update_views.py $@"
date;time nice uv run python update_views.py $@
