#!/bin/bash
# Install TADA only provisioned Valley or Mountain host

cd /opt/tada
source /opt/tada/venv/bin/activate
/opt/tada/venv/bin/python3 setup.py install --force
installTadaTables
