#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test; 
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.direct_submit.sh
# This file tests DIRECT submit (no queue, no valley) of:
#   1. non-FITS; (reject, not try to ingest)
#   2. compliant FITS with no options (no need for them, so iongest success)
#   3. non-compliant FITS (ingest failure)
#   4. FITS made compliant via passed personality options (ingest success)
#

cmd=`basename $0`


SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
tdata=$SCRIPTDIR/tada-test-data
# tdata=/sandbox/tada/tests/smoke/data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/../tada-cli/scripts:$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.pipeline_submit.txt"

echo ""
echo "Starting tests in \"smoke.pipeline_submit.sh\" ..."
echo ""
echo ""
source tada-smoke-setup.sh

testCommand ps1_1 "fsub $tdata/basic/uofa-mandle.jpg pipeline-mosaic3" "^\#" n 1
testCommand ps2_1 "fsub $tdata/basic/obj_355_VR_v1.fits.fz pipeline-mosaic3" "^\#" n

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
exit $return_code

