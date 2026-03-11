#!/bin/bash
# time scripts/run_update_topitems.sh samples/logan.yml $HOME/anomdec/topitems.json

if [ $# -ne 2 ]; then
    echo "Usage: $0 config_path report_path"
    exit 1
fi
config_path=$1
report_path=$2

if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi
end=$(date +"%s")
end=$(expr $end - 600)
echo "$(date) uv run python update_topitems.py -c $config_path --end $end --output $report_path"
date;time nice uv run python update_topitems.py -c $config_path --end $end --output $report_path

echo completed
