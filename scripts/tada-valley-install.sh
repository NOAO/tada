#!/bin/bash
# Install TADA on provisioned Valley or Mountain host
# run as: tada
# Used by puppet

LOG="/etc/tada/install.log"
date > $LOG

cd /opt/tada
source /opt/tada/venv/bin/activate
/opt/tada/venv/bin/python3 setup.py install --force >> $LOG
installTadaTables >> $LOG
