#!/bin/bash
# time scripts/run_hourly_detection.sh samples/unified.yml $HOME/anomdec

if [ $# -ne 2 ]; then
    echo "Usage: $0 config_path report_path"
    exit 1
fi
config_path=$1
report_dir=$2

source $HOME/venv/bin/activate
if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi
end=$(date +"%s")
end=$(expr $end - 600)
echo "$(date) python3 detect_anomalies.py -c $config_path --end $end --output $report_dir/detection.json"
date;time nice python3 detect_anomalies.py -c $config_path --end $end --output $report_dir/detection.json

echo "$(date) python3 update_views.py -c $config_path"
date;time nice python3 update_views.py -c $config_path

echo "date;time nice python3 reporter.py -c $config_path --end $end --output $report_dir/report.json"
date;time nice python3 reporter.py -c $config_path --end $end --output $report_dir/report.json

echo completed
