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
tdata=$SCRIPTDIR/tada-test-data
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

tic=`date +'%s'`

MAX_DROP_WAIT_TIME=10  # max seconds from file drop to ingest/reject

sdrop=$tdata/scrape
# fail-fail (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
testCommand db1_1 "faildrop $sdrop/20110101/wiyn-bench/24dec_2014.061.fits.fz 20110101 wiyn-bench" "^\#" y 0

# fail-pass (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
testCommand db1_2 "passdrop $sdrop/20160314/kp4m-mosaic3/mos3.75870.fits.fz 20160314 kp4m-mosaic3" "^\#" y 0

# pass-pass (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
testCommand db1_3 "passdrop $sdrop/20150709/bok23m-90prime/d7212.0062.fits.fz 20150709 bok23m-90prime" "^\#" n 0

###########################################
echo "WARNING: ignoring remainder of tests"
exit $return_code
###########################################a

sdrop=$tdata/short-drop
testCommand db2_1 "faildrop $sdrop/bad-date/wiyn-whirc/obj_355a.fits.fz bad-date wiyn-whirc" "^\#" n 9
testCommand db2_2 "faildrop $sdrop/20160909/bad-instrum/obj_355b.fits.fz 20160909 bad-instrum" "^\#" n 9
testCommand db2_3 "passdrop $sdrop/20141220/wiyn-whirc/obj_355.fits.fz 20141220 wiyn-whirc" "^\#" n 0
testCommand db2_4 "passdrop $sdrop/20160610/kp4m-mosaic3/mos3.94567.fits 20160610 kp4m-mosaic3" "^\#" n 0 
testCommand db2_5 "faildrop $sdrop/20160610/kp4m-mosaic3/mos3.badprop.fits 20160610 kp4m-mosaic3" "^\#" n 0 
testCommand db2_6 "passdrop $sdrop/20110101/ct13m-andicam/ir141225.0179.fits 20110101 ct13m-andicam" "^\#" n 0 

echo "MAX_FOUND_TIME=$MAX_FOUND_TIME"


emins=$((`date +'%s'` - tic))
# expect about 168 seconds
echo "# Completed dropbox test: " `date` " in $emins seconds"


# Directory structure is wrong! (one too deep)
# scrape/<date>/<instrument>/.../*.fits.fz
#! testCommand db2_1 "mdbox $tdata/scrape" "^\#" n
#! testCommand db2_2 "sbox" "^\#" n



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
