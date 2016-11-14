#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test; 
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.direct_submit.sh
# This file tests DIRECT submit (no queue, no valley)


cmd=`basename $0`


SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
tdata=$SCRIPTDIR/data
# tdata=/sandbox/tada/tests/smoke/data

echo "tadadir=$tadadir, SCRIPTDIR=$SCRIPTDIR"

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.fits_submit.txt"

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

function ingest () {
    ffile=$1; shift
    pers=""
    for p; do
	pers="$pers -p $p"
    done
	
    fits_submit -p smoke $pers $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}


## non-FITS; (reject, do not try to ingest)
testCommand fs1_1 "ingest $tdata/uofa-mandle.jpg" "^\#" n

## compliant FITS with no options (no need for them, so ingest success)
testCommand fs2_1 "ingest $tdata/k4k_140922_234607_zri.fits.fz" "^\#" n

## bad format for DATE-OBS
testCommand fs3_1 "ingest $tdata/kp109391.fits.fz" "^\#" n

## FITS made compliant via passed personality options; compress on-the-fly
## (ingest success)
testCommand fs4_1 "ingest $tdata/obj_355.fits wiyn-whirc" "^\#" n


## FITS made compliant via passed personality options; multi-extensions
## (ingest success)
testCommand fs5_1 "ingest $tdata/obj_355.fits.fz wiyn-whirc" "^\#" n

## non-compliant FITS (ingest failure)

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

