#!/bin/bash
# Update TADA tables from MARS and restart
# run as sudo

SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in


$SCRIPTDIR/installTadaTables
service dqd restart

echo "TADA tables have been installed from MARS and dqd restarted."
