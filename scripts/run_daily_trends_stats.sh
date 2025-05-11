#!/bin/bash
# time scripts/run_daily_trends_stats.sh -c samples/unified.yml --init --output $HOME/anomdec/trend_stats.json
source $HOME/venv/bin/activate
if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi
end=$(date +"%s")
end=$(expr $end - 3600)
python3 trends_stats.py --end $end $@ 