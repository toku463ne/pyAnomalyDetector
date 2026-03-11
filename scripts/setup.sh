#!/bin/bash

envfile=$1
if [ "$envfile" == "" ]; then
    envfile="scripts/setup.env"
fi
source $envfile

script_folder=$(dirname "$(realpath "$0")")
#cd $script_folder

set -eu

# install python uv if not already installed
if ! command -v uv &> /dev/null
then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo source $HOME/.local/bin/env
source $HOME/.local/bin/env

echo uv sync
uv sync


# register the streamlit service
#uv run python tools/render_template.py templates/systemd_streamlit.service.j2 /etc/systemd/system/streamlit.service

#systemctl daemon-reload
#systemctl enable streamlit.service
#systemctl start streamlit.service

echo "Setup complete. Virtual environment created and dependencies installed."
