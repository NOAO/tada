#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test;

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
SMOKEOUT="README-smoke-results.fits_submit.txt"

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

###########################################
### fits_compliant
###

## bad DATE-OBS content
testCommand fc1_1 "fits_compliant --header $tdata/kp109391.fits.fz" "^\#" n

# missing raw
testCommand fc2_1 "fits_compliant $tdata/kptest.fits" "^\#" n

###########################################
### fits_submit
###
function fsubmit () {
    ffile=$1; shift
    pers=""
    for p; do
	pers="$pers -p $p"
    done
    fits_submit -p smoke $pers $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}


## non-FITS; (reject, not try to ingest)
testCommand fs1_1 "fsubmit $tdata/uofa-mandle.jpg" "^\#" n

## compliant FITS with no options (no need for them, so ingest success)
testCommand fs2_1 "fsubmit $tdata/k4k_140922_234607_zri.fits.fz" "^\#" n

## bad format for DATE-OBS
testCommand fs3_1 "fsubmit $tdata/kp109391.fits.fz" "^\#" n

## FITS made compliant via passed personality options; compress on-the-fly
## (ingest success)
testCommand fs4_1 "fsubmit $tdata/obj_355.fits wiyn-whirc" "^\#" n


## FITS made compliant via passed personality options; multi-extensions
## (ingest success)
testCommand fs5_1 "fsubmit $tdata/obj_355.fits.fz wiyn-whirc" "^\#" n

## non-compliant FITS, missing RAW (ingest failure)
testCommand fs6_1 "fsubmit $tdata/kptest.fits" "^\#" n

###########################################
### pipeline_submit
###
function psubmit () {
    ffile=$1; shift
    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}

testCommand ps1_1 "psubmit $tdata/uofa-mandle.jpg" "^\#" n
testCommand ps2_1 "psubmit $tdata/c4d_130901_031805_oow_g_d2.fits.fz" "^\#" n



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

