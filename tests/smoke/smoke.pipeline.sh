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
tdata=/data/tada-test-data
ppath=/var/tada/personalities

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/../tada-cli/scripts:$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.pipeline.txt"

echo ""
echo "Starting tests in \"smoke.pipeline.sh\" [allow 1 minutes] ..."
echo ""
echo ""
source tada-smoke-setup.sh

testCommand ps1_1 "fsub $tdata/basic/uofa-mandle.jpg pipeline-mosaic3" "^\#" n 1
testCommand ps2_1 "fsub $tdata/basic/obj_355_VR_v1_TADAPIPE.fits.fz pipeline-mosaic3" "^\#" n

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################

#!###########################################
#!### pipeline_submit
#!###
#!function psubmit () {
#!    ffile=$1; shift
#!    #msg=`pipeline_submit $ffile 2>&1`
#!    #!status=$?
#!    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
#!}
#!
#!testCommand ps1_1 "psubmit $tdata/basic/uofa-mandle.jpg" "^\#" n
#!testCommand ps2_1 "psubmit $tdata/basic/c4d_130901_031805_oow_g_d2.fits.fz" "^\#" n


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




