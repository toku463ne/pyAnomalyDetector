#!/bin/bash
# time scripts/run_hourly_detection.sh samples/zabbix.yml $HOME/anomdec/report.json

if [ $# -ne 2 ]; then
    echo "Usage: $0 config_path report_path"
    exit 1
fi
config_path=$1
report_path=$2

source $HOME/venv/bin/activate
if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi


end=$(date +"%s")
end=$(expr $end - 600)
echo date;time nice python3 reporter.py -c $config_path --output $report_path  --end $end
date;time nice python3 reporter.py -c $config_path --output $report_path  --end $end

echo completed
