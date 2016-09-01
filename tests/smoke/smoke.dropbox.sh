#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
#   Use mountain dropbox to ingest set files files. Run from Valley.
#   The tricky part of tests is need to test for ingest fail conditions.
#   We want to prove that:
#     - bad input fails in expected way (including reporting of error/warning)
#     - good input ingests
#
#   The "dropbox" is a directory that is monitored for fits files
#   appearing in it. Any that appear and match "*.fits.fz" or "*.fits"
#   are submitted for ingest.
#
# WARNING: combining multiple dropbox tests can result in filename collisions
# (even between "different" names such as myfile.fits and myfile.fits.fz)
# The result will depend on timing!  So eliminate filename collisions across tests!

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
#tdata=$SCRIPTDIR/tada-test-data
tdata=/data/tada-test-data
# tdata=/sandbox/tada/tests/smoke/tada-test-data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH
export PATH=$tadadir/../tada-cli/scripts:$PATH

source smoke-lib.sh

return_code=0
SMOKEOUT="README-smoke-results.dropbox.txt"

echo "# "
echo "# Starting tests in \"smoke.dropbox.sh\" ..."
echo "# "
source tada-smoke-setup.sh
source dropsub.sh
setup_dropbox_tests

SRCFILES=""

##############################################################################
## Transfer of FITS happens only after validation checks.  Better if valid fits
## are small to keep run-time (due to transfer) of smoke tests low.
##
tic=`date +'%s'`
MAX_DROP_WAIT_TIME=10  # max seconds from file drop to ingest/reject
#MAX_DROP_WAIT_TIME=600  # max seconds from file drop to ingest/reject
plog="/var/log/tada/pop.log"
MARKER="`date '+%Y-%m-%d %H:%M:%S'` START-SMOKE-TEST"
echo $MARKER >> $plog
FTO=5 # fail timeout



# fail-fail (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
FITS="$tdata/scrape/20110101/wiyn-bench/24dec_2014.061.fits.fz"
testCommand db1_1 "faildrop $FTO $FITS 20110101 wiyn-bench" "^\#" n 0
testLog db1_1_log  "pylogfilter $plog \"$MARKER\" $FITS"

# pass-pass
#!FITS="$tdata/scrape/20110101/ct13m-andicam/ir141225.0179.fits.fz"
#!testCommand db1_3 "faildrop $FTO $FITS 20110101 ct13m-andicam" "^\#" n 0
FITS="$tdata/basic/kp109391.fits.fz"
testCommand db1_3 "faildrop $FTO $FITS 20110101 kp4m-kosmos" "^\#" n 0

###########################################
echo "WARNING: ignoring remainder of tests"
exit $return_code
###########################################a


FITS=$tdata/short-drop/bad-date/wiyn-whirc/obj_355a.fits.fz
testCommand db2_1 "faildrop $FTO $FITS bad-date wiyn-whirc" "^\#" n 9
testLog db2_1_log $plog "pylogfilter $MARKER $FITS"

FITS=$tdata/short-drop/20160909/bad-instrum/obj_355b.fits.fz
testCommand db2_2 "faildrop $FTO $FITS 20160909 bad-instrum" "^\#" n 9
testLog db2_2_log $plog "pylogfilter $MARKER $FITS"

#!testCommand db2_3 "passdrop $tdata/short-drop/20141220/wiyn-whirc/obj_355.fits.fz 20141220 wiyn-whirc" "^\#" n 0
#!testCommand db2_4 "passdrop $tdata/short-drop/20160610/kp4m-mosaic3/mos3.94567.fits 20160610 kp4m-mosaic3" "^\#" n 0 

FITS=$tdata/short-drop/20160610/kp4m-mosaic3/mos3.badprop.fits
testCommand db2_5 "faildrop $FTO $FITS  20160610 kp4m-mosaic3" "^\#" n 0 
testLog db2_5_log $plog "pylogfilter $MARKER $FITS"

#!testCommand db2_6 "passdrop $tdata/short-drop/20110101/ct13m-andicam/ir141225.0179.fits 20110101 ct13m-andicam" "^\#" n 0 

# fail-pass 
FITS="$tdata/scrape/20160314/kp4m-mosaic3/mos3.75870.fits.fz"
testCommand db1_2 "passdrop 20 $FITS 20160314 kp4m-mosaic3" "^\#" n 0
testLog db1_2_log $plog "pylogfilter $MARKER $FITS"


# Directory structure is wrong! (one too deep)
# scrape/<date>/<instrument>/.../*.fits.fz
#! testCommand db2_1 "mdbox $tdata/scrape" "^\#" n
#! testCommand db2_2 "sbox" "^\#" n

##############################################################################

echo "MAX_FOUND_TIME=$MAX_FOUND_TIME"
emins=$((`date +'%s'` - tic))
# expect about 168 seconds
echo "# Completed dropbox test: " `date` " in $emins seconds"

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

##############################################################################
# Don't move or remove! 
cd $origdir
#exit $return_code
return $return_cod
