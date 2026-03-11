#!/bin/bash
# time scripts/run_hourly_detection.sh samples/unified.yml $HOME/anomdec

if [ $# -ne 2 ]; then
    echo "Usage: $0 config_path report_path"
    exit 1
fi
config_path=$1
report_dir=$2

unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi
end=$(date +"%s")
end=$(expr $end - 600)
echo "$(date) uv run python detect_anomalies.py -c $config_path --end $end --output $report_dir/detection.json"
date;time nice uv run python detect_anomalies.py -c $config_path --end $end --output $report_dir/detection.json

echo "$(date) uv run python update_views.py -c $config_path"
date;time nice uv run python update_views.py -c $config_path

echo "$(date) uv run python reporter.py -c $config_path --end $end --output $report_dir/report.json"
date;time nice uv run python reporter.py -c $config_path --end $end --output $report_dir/report.json

echo completed
