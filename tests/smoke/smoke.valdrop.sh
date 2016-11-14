#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Test using Valley dropbox (intended for pipeline workflow)
#  Like smoke.dropbox.sh but sends files to valley
#  # NO:Unlike smoke.dropbox.sh, this sends a whole batch of files at once.

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
export PATH=$tadadir/../tada-cli/scripts:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.valdrop.txt"

echo ""
echo "# Starting \"smoke.dropbox.sh\" on `date` ..."
echo ""
source tada-smoke-setup.sh
source dropsub.sh
setup_dropbox_tests

####################
## Transfer of FITS happens only after validation checks.  Better if valid fits
## are small to keep run-time (due to transfer) of smoke tests low.
##
tic=`date +'%s'`
MAX_DROP_WAIT_TIME=10  # max seconds from file drop to ingest/reject
plog="/var/log/tada/pop.log"
MARKER="`date '+%Y-%m-%d %H:%M:%S'` START-SMOKE-TEST"
echo $MARKER >> $plog
FTO=10 # timeout to use when we expect ingest failure; driven by webservices?
# To estimate timeout for FITS transfer use dropsub.sh:up_secs



#testCommand vd1_1 "dropdir $tdata/drop-test" "^\#" y 0

##############################################################################
### Tests
#DROPHOST=`grep valley_host /etc/tada/hiera.yaml | cut -d' ' -f2`
DROPHOST="$VALHOST"
echo "# Using DROPHOST=$DROPHOST"

# fail-fail (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
FITS="$tdata/scrape/20110101/wiyn-bench/24dec_2014.061.fits.fz"
testCommand vdb1_1 "faildrop $FTO $FITS 20110101 wiyn-bench" "^\#" n 0
testLog vdb1_1_log "pylogfilter $plog \"$MARKER\" $FITS"

# pass-pass fitsverify
# uncompressed (compress on the fly); allow extra time for compression
FITS=$tdata/short-drop/20110101/ct13m-andicam/ir141225.0179.fits
testCommand vdb2_6 "passdrop 10 $FITS 20110101 ct13m-andicam" "^\#" n 0 
testLog vdb2_6_log "pylogfilter $plog \"$MARKER\" $FITS"


############
### All three (obj_355, obj_355a, obj_355b) have same checksum!!!
### Causes trouble with collisions (on dq, auditdb)
###
# Will not have a personality for "bad-instrum" (tele-instrum)
# when monitor needs it.  So fail on MOUNTAIN hence timeout on valley.
FITS=$tdata/short-drop/20160909/bad-instrum/obj_355b.fits.fz
testCommand vdb2_2 "dropfile $FTO $FITS 20160909 bad-instrum 1" "^\#" n 9
testLog vdb2_2_log "pylogfilter $plog \"$MARKER\" $FITS"

FITS=$tdata/short-drop/20141220/wiyn-whirc/obj_355.fits.fz
testCommand vdb2_3 "passdrop 10 $FITS 20141220 wiyn-whirc" "^\#" n 0
testLog vdb2_3_log "pylogfilter $plog \"$MARKER\" $FITS"
### 
############

FITS=$tdata/short-drop/20160610/kp4m-mosaic3/mos3.badprop.fits
testCommand vdb2_5 "faildrop 7 $FITS 20160610 kp4m-mosaic3" "^\#" n 0 
testLog vdb2_5_log "pylogfilter $plog \"$MARKER\" $FITS"

# This one takes longish! Could not find smaller file that astropy fixes
# (original fails fitsverify, to-be-ingested passes verify)
# 57 seconds to iputr 71,222,400 bytes @ 10mbps
# fail-pass fitsverify
FITS="$tdata/scrape/20160314/kp4m-mosaic3/mos3.75870.fits.fz"
testCommand vdb1_2 "passdrop 70 $FITS 20160314 kp4m-mosaic3" "^\#" n 0
testLog vdb1_2_log "pylogfilter $plog \"$MARKER\" $FITS"

#########################
# TODO: Summary check. We expect:  !!!
#  3 INFO "SUCCESSFUL submit_to_archive"
#  2 ERROR IngestRejection
#  2 WARNING 
testLog vdb3_1_log "pylogrun $plog \"$MARKER\""

# Verify behavior on DROPBOX machine. 
# (see watch.log)
FITS=$tdata/short-drop/bad-date/wiyn-whirc/obj_355a.fits.fz
testCommand vdb2_1 "faildrop $FTO $FITS bad-date wiyn-whirc" "^\#" n 9
testLog vdb2_1_log  "pylogfilter $plog \"$MARKER\" $FITS"

#!rsync -az --password-file ~/.tada/rsync.pwd tada@mountain.test.noao.edu::logs ~/.tada/mountain-logs
#!testLog vdb4_1_log "mtnlogrun $mtn_plog ${mtn_plog_start}"
#!testLog vdb5_1_log "mtnlogrun $mtn_wlog ${mtn_wlog_start}"

# Directory structure is wrong! (one too deep) TEST ON MOUNTAIN
# scrape/<date>/<instrument>/.../*.fits.fz
#! testCommand vdb2_2 "mdbox $tdata/scrape" "^\#" n
#! testCommand vdb2_2 "sbox" "^\#" n

# TOO LONG!!! Almost 4 minutes to transfer
#! FITS=$tdata/short-drop/20160610/kp4m-mosaic3/mos3.94567.fits
#! testCommand vdb2_4 "passdrop 230 $FITS 20160610 kp4m-mosaic3" "^\#" n 0 

###
##############################################################################

echo "MAX_FOUND_TIME=$MAX_FOUND_TIME"
emins=$((`date +'%s'` - tic))
echo "# Completed dropbox test: " `date` " in $emins seconds"


###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################


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
