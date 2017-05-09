#!/bin/bash
# Install TADA on provisioned Valley or Mountain host
# run as: tada
# run from directory top of installed tada repo, contianing venv subdir
# Used by puppet
#
# To use this in DEV, do: "vagrant provision valley mountain"

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


#!sudo rm /var/log/tada/*.err
#!sudo service dqd restart > /dev/null
#!if [ -s /var/log/tada/dqd.err ]; then
#!    cat /var/log/tada/dqd.err
#!    echo "ERROR: The 'dqd' service is not running"
#!    exit 1
#!else
#!    echo "dqd restarted successfully."
#!    #!sudo dqcli --clear
#!    dqcli --clear
#!fi
#!
#!sudo service watchpushd restart > /dev/null
#!if [ -s /var/log/tada/watchpushd.err ]; then
#!    cat /var/log/tada/watchpushd.err
#!    echo "ERROR: The 'watchpushd' service is not running"
#!    exit 1
#!else
#!	echo "watchpushd restarted successfully"
#!fi

cat $LOG
