#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Make sure hosts and services are running for TADA tests!
# EXAMPLE:

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.pipeline.txt"

echo ""
echo "Starting tests in \"smoke.system.sh\" [allow 1 minutes] ..."
echo ""
echo ""
source /etc/tada/smoke-config.sh

failcnt=0

for host in $ARCHHOST $IRODSHOST $DQHOST $MARSHOST $MTNHOST
do
    totalcnt=$((totalcnt + 1))    
    if ! ping -c 1 -w 1 $host > /dev/null; then
        echo "Host not alive per ping: $host"
	failcnt=$((failcnt + 1))
    fi
done

if [ $failcnt -gt 0 ]; then
    exit 9
fi


#testCommand ps1_1 "fsub $tdata/basic/uofa-mandle.jpg pipeline-mosaic3" "^\#" n 1

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################
