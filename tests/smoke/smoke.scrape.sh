#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test;

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
#!tdata=$SCRIPTDIR/data-scrape
# tdata=/sandbox/tada/tests/smoke/tada-test-data/scrape
#tdata=$SCRIPTDIR/tada-test-data/scrape
tdata=/data/tada-test-data/scrape
#echo "tdata=$tdata; tadadir=$tadadir; SCRIPTDIR=$SCRIPTDIR"
ppath=/var/tada/personalities

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.scrape.txt"

echo "# "
echo "# Starting tests in \"smoke.scrape.sh\" [allow 8 minutes] ..."
echo "# "
source tada-smoke-setup.sh

echo "Doing 17 tests (using scraped files)"    


###########################################
#echo "WARNING: ignoring remainder of tests"
#exit $return_code
###########################################a


testCommand sc1_1  "fsub $tdata/20150709/bok23m-90prime/d7212.0062.fits.fz bok23m-90prime" "^\#" n
testCommand sc2_1  "fsub $tdata/20110101/ct13m-andicam/ir141225.0179.fits.fz ct13m-andicam" "^\#" n
testCommand sc3_1  "fsub $tdata/20110101/ct15m-echelle/chi150724.1000.fits.fz ct15m-echelle" "^\#" n
testCommand sc4_1  "fsub $tdata/20150705/ct4m-cosmos/n3.25523.fits.fz ct4m-cosmos" "^\#" n
testCommand sc5_1  "fsub $tdata/20151007/ct4m-decam/DECam_00482540.fits.fz ct4m-decam " "^\#" n
testCommand sc6_1  "fsub $tdata/20141224/kp09m-hdi/c7015t0267b00.fits.fz kp09m-hdi" "^\#" n
#!testCommand sc7_1  "fsub $tdata/20141215/kp4m-mosaic_1_1/spw54553.fits.fz kp4m-mosaic_1_1" "^\#" n
testCommand sc7_1  "fsub $tdata/20160314/kp4m-mosaic3/mos3.75870.fits.fz  kp4m-mosaic3" "^\#" n
testCommand sc8_1  "fsub $tdata/20141215/kp4m-newfirm/nhs_2015_n04_319685.fits.fz kp4m-newfirm" "^\#" n
testCommand sc9_1  "fsub $tdata/20110101/soar-goodman/0079.spec_flat.fits.fz soar-goodman" "^\#" n
#soar-osiris  # scrape has no "passable" files for this instrument
#soar-sami    # scrape has no "passable" files for this instrument
testCommand sc16_1 "fsub $tdata/20110101/soar-sami/SO2016B-015.013.fits.fz soar-sami" "^\#" n
testCommand sc10_1 "fsub $tdata/20110101/soar-spartan/011-6365d0.fits.fz soar-spartan" "^\#" n
testCommand sc10_1a "fsub $tdata/20110101/soar-spartan/S301D_K012-0484d0.fits.fz soar-spartan" "^\#" n
testCommand sc10_1b "fsub $tdata/20110101/soar-spartan/S301D_K012-0484d3.fits.fz soar-spartan" "^\#" n
testCommand sc11_1 "fsub $tdata/20110101/wiyn-bench/24dec_2014.061.fits.fz wiyn-bench" "^\#" n 0
testCommand sc12_1 "fsub $tdata/20110101/wiyn-whirc/obj_355.fits.fz wiyn-whirc" "^\#" n
testCommand sc13_1 "fsub $tdata/20150929/kp4m-kosmos/a.20153.fits.fz kp4m-kosmos" "^\#" n
testCommand sc14_1 "fsub $tdata/20141127/soar-soi/test.027.fits.fz soar-soi" "^\#" n 0
testCommand sc15_1 "fsub $tdata/20160315/ct4m-arcoiris/SV_f0064.fits ct4m-arcoiris" "^\#" n



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
#exit $return_code
return $return_code
