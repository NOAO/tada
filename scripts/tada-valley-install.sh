#!/bin/bash
# Install TADA on provisioned Valley or Mountain host
# run as: tada
# run from directory top of installed tada repo, contianing venv subdir
# Used by puppet

VERSION=`cat tada/VERSION`

LOG="install.log"
date                              > $LOG
source /opt/tada/venv/bin/activate

dir=`pwd`
#e.g. cd /opt/tada
echo "Running install on dir: $dir"
python3 setup.py install --force >> $LOG
installTadaTables                >> $LOG
echo "Installed TADA version: $VERSION" >> $LOG
cat $LOG
