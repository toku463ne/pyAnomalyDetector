#!/bin/bash

script_folder=$(dirname "$(realpath "$0")")
cd $script_folder

# Update package lists
sudo apt-get update

# Install Python3 and pip
sudo apt-get install -y python3 python3-pip

# Install virtualenv
pip3 install virtualenv

# Create a virtual environment
virtualenv venv

# Activate the virtual environment
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt

# Compile cython codes
#python setup.py build_ext --inplace


echo "Setup complete. Virtual environment created and dependencies installed."