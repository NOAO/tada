#!/bin/bash
# Install TADA on provisioned Valley or Mountain host
# run as: tada

cd /opt/tada
source /opt/tada/venv/bin/activate
/opt/tada/venv/bin/python3 setup.py install --force
installTadaTables
