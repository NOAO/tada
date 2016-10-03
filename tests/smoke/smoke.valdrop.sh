#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Test using Valley dropbox (intended for pipeline workflow)
#  Unlike smoke.dropbox.sh, this sends a whole batch of files at once.

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
tdata=/data/tada-test-data
ppath=/var/tada/personalities

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/../tada-cli/scripts:$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.pipeline.txt"

echo ""
echo "Starting tests in \"smoke.valdrop.sh\" [allow 1 minutes] ..."
echo ""
echo ""
source tada-smoke-setup.sh
source dropsub.sh
setup_dropbox_tests


testCommand vd1_1 "dropdir $tdata/drop-test" "^\#" y 0

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################


##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
    echo ""
    echo "ALL $totalcnt smoke tests PASSED ($SMOKEOUT created)"
    echo "All $totalcnt tests passed on " `date` > $SMOKEOUT
else
    echo "Smoke FAILED $failcnt/$totalcnt (no $SMOKEOUT produced)"
fi


# Don't move or remove! 
cd $origdir
#exit $return_code
return $return_code
