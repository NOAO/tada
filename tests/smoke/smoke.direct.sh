#!/bin/bash 
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test;

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
tdata=$SCRIPTDIR/data
# tdata=/sandbox/tada/tests/smoke/data

echo "tdata=$tdata; tadadir=$tadadir; SCRIPTDIR=$SCRIPTDIR"

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.fits_submit.txt"

echo ""
echo "Starting tests in \"$SCRIPT\" ..."
echo ""
if curl -s -S "http://mars.sdm.noao.edu:8000/provisional/rollback/" > /dev/null
then
    echo "REMOVED all provisional files before starting."
else
    echo "COULD NOT remove all provisional files before starting."    
fi
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
    #!fits_submit -p smoke $pers $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
    msg=`fits_submit -p smoke $pers $ffile 2>&1`
    status=$?
    if [ $status -eq 0 ]; then
        # e.g. msg="SUCCESS: archived /sandbox/tada/tests/smoke/data/obj_355.fits as /noao-tuc-z1/mtn/20141219/WIYN/2012B-0500/uuuu_141220_130138_uuu_TADATEST_2417885023.fits"
        irodsfile=`echo $msg | cut -s --delimiter=' ' --fields=5`
        archfile=`basename $irodsfile`
        echo $msg 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
        curl -s -S "http://mars.sdm.noao.edu:8000/provisional/add/$archfile/?source=$ffile"
        echo ""
        echo "Successful ingest. Added $archfile to PROVISIONAL list via ws"
    else
        #! >&2 echo "EXECUTED: fits_submit -p smoke $pers $ffile"  
        #! >&2 echo $msg
        echo "EXECUTED: fits_submit -p smoke $pers $ffile"  
        echo $msg
    fi
    return $status
}


## non-FITS; (reject, not try to ingest)
testCommand fs1_1 "fsubmit $tdata/uofa-mandle.jpg" "^\#" n 1

## compliant FITS with no options (no need for them, so ingest success)
testCommand fs2_1 "fsubmit $tdata/k4k_140922_234607_zri.fits.fz" "^\#" n

## compliant FITS with no options (BUT, already inserted above so ingest FAIL)
testCommand fs2b_1 "fsubmit $tdata/k4k_140922_234607_zri.fits.fz" "^\#" n 2

## bad format for DATE-OBS
testCommand fs3_1 "fsubmit $tdata/kp109391.fits.fz" "^\#"  n 2

## FITS made compliant via passed personality options; compress on-the-fly
## (ingest success)
testCommand fs4_1 "fsubmit $tdata/obj_355.fits wiyn-whirc" "^\#" n

## FITS made compliant via passed personality options; multi-extensions
## (ingest success)
testCommand fs5_1 "fsubmit $tdata/obj_355.fits.fz wiyn-whirc" "^\#" n

## non-compliant FITS, missing RAW (ingest failure)
testCommand fs6_1 "fsubmit $tdata/kptest.fits" "^\#" n 1

###########################################
### pipeline_submit
###
function psubmit () {
    ffile=$1; shift
    #msg=`pipeline_submit $ffile 2>&1`
    #!status=$?
    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}

testCommand ps1_1 "psubmit $tdata/uofa-mandle.jpg" "^\#" n
testCommand ps2_1 "psubmit $tdata/c4d_130901_031805_oow_g_d2.fits.fz" "^\#" n




###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a


##############################################################################

#!if curl -s -S "http://mars.sdm.noao.edu:8000/provisional/stuff/" > /dev/null
#!then
#!    echo "STUFFED all references containing 'TADA' into provisional."
#!else
#!    echo "COULD NOT stuff references containing 'TADA' into provisional."
#!fi


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

