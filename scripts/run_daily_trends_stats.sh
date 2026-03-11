#!/bin/bash
#

unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

if [ "$ANOMDEC_SECRET_PATH" == "" ]; then
    export ANOMDEC_SECRET_PATH="$HOME/.creds/anomdec.yaml"
fi
end=$(date +"%s")
end=$(expr $end - 3600)
#python3 trends_stats.py --end $end $@ 
uv run python trends_stats.py --end $end $@ 

