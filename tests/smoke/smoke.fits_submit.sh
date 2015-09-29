#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test; 
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.direct_submit.sh
# This file tests DIRECT submit (no queue, no valley) of:
#   (1. non-FITS; NOT APPLICABLE)
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
SMOKEOUT="README-smoke-results.txt"

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

optprms="-o __jobid_type=seconds"


function ingest () {
    ffile=$1
    fits_submit -p smoke $ffile 2>&1 | perl -pe 's/as *//'
}

##########################
# 2_1: pass ingest without options
testCommand fs2_1 "fits_submit -p smoke $tdata/k4k_140922_234607_zri.fits.fz 2>&1" "^\#" y


##########################
# 3_1: fail ingest
testCommand fs3_1 "fits_submit -p smoke $tdata/kp109391.fits.fz 2>&1" "^\#" y


##########################
# 4_1: pass ingest using options
testCommand fs4_1 "fits_submit -p smoke $tdata/obj_355.fits  2>&1" "^\#" y

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

