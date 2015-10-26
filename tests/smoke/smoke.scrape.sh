#!/bin/bash 
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test;

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
tdata=$SCRIPTDIR/data-scrape
# tdata=/sandbox/tada/tests/smoke/data-scrape

echo "tdata=$tdata; tadadir=$tadadir; SCRIPTDIR=$SCRIPTDIR"

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.scrape.txt"

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
### fits_submit
###
function fsub () {
    pers=$1
    ffile=$2

    msg=`fits_submit -p smoke -p $pers $ffile 2>&1`
    status=$?
    if [ $status -eq 0 ]; then
        irodsfile=`echo $msg | cut -s --delimiter=' ' --fields=5`
        archfile=`basename $irodsfile`
        echo $msg 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
        curl -s -S "http://mars.sdm.noao.edu:8000/provisional/add/$archfile/?source=$ffile"
        echo ""
        echo "Successful ingest. Added $archfile to PROVISIONAL list via ws"
    else
        echo "EXECUTED: fits_submit -p smoke $pers $ffile"  
        echo $msg
    fi
    return $status
}



testCommand sc1_1  "fsub bok23m-90prime $tdata/bok23m-90prime/d7212.0062.fits.fz" "^\#" n
testCommand sc2_1  "fsub ct13m-andicam $tdata/ct13m-andicam/ir141225.0179.fits.fz" "^\#" n
testCommand sc3_1  "fsub ct15m-echelle $tdata/ct15m-echelle/chi150724.1000.fits.fz" "^\#" n
testCommand sc4_1  "fsub ct4m-cosmos $tdata/ct4m-cosmos/n3.25523.fits.fz" "^\#" n
testCommand sc5_1  "fsub ct4m-decam  $tdata/ct4m-decam//DECam_00482540.fits.fz" "^\#" n
testCommand sc6_1  "fsub kp09m-hdi $tdata/kp09m-hdi/c7015t0267b00.fits.fz" "^\#" n
testCommand sc13_1 "fsub kp4m-kosmos $tdata/kp4m-kosmos/a.20153.fits.fz" "^\#" n
testCommand sc7_1  "fsub kp4m-mosaic_1_1 $tdata/kp4m-mosaic_1_1/spw54553.fits.fz" "^\#" n
testCommand sc8_1  "fsub kp4m-newfirm $tdata/kp4m-newfirm/nhs_2015_n04_319685.fits.fz" "^\#" n
testCommand sc9_1  "fsub soar-goodman $tdata/soar-goodman/0079.spec_flat.fits.fz" "^\#" n
#soar-osiris  # scrape has no "passable" files for this instrument
#soar-sami    # scrape has no "passable" files for this instrument
testCommand sc14_1 "fsub soar-soi $tdata/soar-soi/test.027.fits.fz" "^\#" n
testCommand sc10_1 "fsub soar-spartan $tdata/soar-spartan/011-6365d0.fits.fz" "^\#" n
testCommand sc11_1 "fsub wiyn-bench $tdata/wiyn-bench/24dec_2014.061.fits.fz" "^\#" n
testCommand sc12_1 "fsub wiyn-whirc $tdata/wiyn-whirc/obj_355.fits.fz" "^\#" n



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

