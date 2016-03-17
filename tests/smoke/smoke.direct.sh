#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
#   Quickest test done on valley to test:
#      A. fits_complaint(2); 
#      B. fits_submit(6);
#      C. pipeline_submit(2);

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
#tdata=$SCRIPTDIR/data
tdata=$SCRIPTDIR/tada-test-data
# tdata=/sandbox/tada/tests/smoke/tada-test-data

# echo "tdata=$tdata; tadadir=$tadadir; SCRIPTDIR=$SCRIPTDIR"

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.direct.txt"

echo "# "
echo "# Starting tests in \"smoke.direct.sh\" ..."
echo "# "
source tada-smoke-setup.sh


##############################################################################


## bad DATE-OBS content
testCommand fc1_1 "fcom $tdata/basic/kp109391.fits.fz" "^\#" n 1

# compliant
testCommand fc2_1 "fcom $tdata/basic/kptest.fits" "^\#" n

# fpack on the fly
unpacked="$tdata/scrape/20160314/kp4m-mosaic3/mos3.75675.fits  kp4m-mosaic3"
testCommand fs0_1 "fsub $unpacked" "^\#" n

## non-FITS; (reject, not try to ingest)
testCommand fs1_1 "fsub $tdata/basic/uofa-mandle.jpg" "^\#" n 1

## compliant FITS with no options (no need for them, so ingest success)
file2="$tdata/basic/cleaned-bok.fits.fz"
testCommand fs2_1 "fsub $file2" "^\#" n

## compliant FITS with no options (BUT, already inserted above so ingest FAIL)
testCommand fs2b_1 "fsub $file2" "^\#" n 2

## bad format for DATE-OBS
testCommand fs3_1 "fsub $tdata/basic/kp109391.fits.fz" "^\#"  n 1

## FITS made compliant via passed personality options; compress on-the-fly
## (ingest success)
testCommand fs4_1 "fsub $tdata/basic/obj_355.fits wiyn-whirc" "^\#" n

## FITS made compliant via passed personality options; multi-extensions
## (ingest success)
testCommand fs5_1 "fsub $tdata/basic/obj_355.fits.fz wiyn-whirc" "^\#" n

## non-compliant FITS, missing RAW (ingest failure)
testCommand fs6_1 "fsub $tdata/basic/kptest.fits" "^\#" n 1

# New instrument <2016-03-17 Thu>
testCommand fs7_1 "fsub $tdata/scrape/20160315/ct4m-arcoiris_spec/SPEC_Eng0246.fits ct4m-arcoiris_spec" "^\#" n


###########################################
### pipeline_submit
###
function psubmit () {
    ffile=$1; shift
    #msg=`pipeline_submit $ffile 2>&1`
    #!status=$?
    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}

#!testCommand ps1_1 "psubmit $tdata/basic/uofa-mandle.jpg" "^\#" n
#!testCommand ps2_1 "psubmit $tdata/basic/c4d_130901_031805_oow_g_d2.fits.fz" "^\#" n


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
#exit $return_code
return $return_code

