#!/bin/bash
if [ $# -ne 2 ]; then
    echo "Usage: $0 config_path report_path"
    exit 1
fi
config_path=$1
report_path=$2

source $HOME/venv/bin/activate
export SECRET_PATH="$HOME/.creds/zabbix_api.yaml"
end=$(date +"%s")
end=$(expr $end - 300)
echo "$(date) python3 detector.py -c $config_path --end $end"
date;time nice python3 detector.py -c $config_path --end $end

echo "$(date) python3 reporter.py -c $config_path --end $end --output $report_path"
date;time nice python3 reporter.py -c $config_path --end $end --output $report_path

echo "$(date) python3 viewer.py -c $config_path"
date;time nice python3 viewer.py -c $config_path

echo "$(date) python3 viewer.py -c $config_path -m bycluster"
date;time nice python3 viewer.py -c $config_path -m bycluster

echo completed
