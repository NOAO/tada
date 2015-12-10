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
tdata=$SCRIPTDIR/data
# tdata=/sandbox/tada/tests/smoke/data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/../tada-cli/scripts:$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.pipeline_submit.txt"

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

function ingest () {
    ffile=$1; shift
    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}


testCommand ps1_1 "ingest $tdata/uofa-mandle.jpg" "^\#" n
testCommand ps2_1 "ingest $tdata/c4d_130901_031805_oow_g_d2.fits.fz" "^\#" n

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a


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

