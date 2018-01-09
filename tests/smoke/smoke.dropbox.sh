#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
#   Use mountain dropbox to ingest files. Run from Valley.
#   These tests must allow time to ingest and test for fail conditions.
#   We want to prove that:
#     - bad input fails in expected way (including reporting of error/warning)
#     - good input ingests
#
# WARNING: combining multiple dropbox tests can result in filename collisions
# (even between "different" names such as myfile.fits and myfile.fits.fz)
# The result will depend on timing!  So eliminate filename collisions across
# tests!

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
# tdata=$SCRIPTDIR/tada-test-data
tdata=/data/tada-test-data
# tdata=/sandbox/tada/tests/smoke/tada-test-data

dir=$SCRIPTDIR
origdir=`pwd`
pushd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH
export PATH=$tadadir/../tada-cli/scripts:$PATH

source smoke-lib.sh

return_code=0
SMOKEOUT="$sto/README-smoke-results.dropbox.txt"

echo "# "
echo "# Starting \"smoke.dropbox.sh\" on `date` ..."
echo "# "
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
echo $MARKER >> /var/log/tada/pop-detail.log
echo "Using log MARKER=$MARKER"
PTO=25 # timeout to use when we expect ingest PASS; driven by webservices?
FTO=20 # timeout to use when we expect ingest FAIL; driven by webservices?
# To estimate timeout for FITS transfer use dropsub.sh:up_secs


mtn_plog=~/.tada/mountain-logs/pop.log
mtn_wlog=~/.tada/mountain-logs/watch.log
rsync -az --password-file ~/.tada/rsync.pwd tada@$MTNHOST::logs ~/.tada/mountain-logs
mtn_plog_start=`cat $mtn_plog | wc -l`
mtn_wlog_start=`cat $mtn_wlog | wc -l`

# Clear MARS log in preparation for counting WARNINGS and ERRORS
curl "http://$MARSHOST:8000/audit/marsclearlog/" > /dev/null 2>&1
curl "http://$MARSHOST:8000/audit/hideall/"      > /dev/null 2>&1


##############################################################################
### Tests



## As of 2/7/2017 this will PASS INGEST because scrub_fits() fixes the header.
#!# fail-fail (fitsverify against 1. mtn dropbox, 2. val to-be-ingested-fits)
#!FITS="$tdata/scrape/20110101/wiyn-bench/24dec_2014.061.fits.fz"
#!testCommand db1_1 "faildrop $FTO $FITS 20110101 wiyn-bench" "^\#" n 0
#!testLog db1_1_log "pylogfilter $plog \"$MARKER\" $FITS"

## success=TRUE
# pass-pass fitsverify
# uncompressed (comprss on the fly) when BITPIX=-32
FITS=$tdata/short-drop/20110101/ct13m-andicam/ir141225.0179.fits
## =>  mtn/20141225/ct13m/smarts/c13a_141226_070040_ori_tTADASMOKE.fits.fz
# "fpack -L" should yield: "tiled_gzip"
testCommand db2_6 "passdrop $PTO $FITS 20110101 ct13m-andicam" "^\#" n 0
#!testLog db2_6_log "pylogfilter $plog \"$MARKER\" $FITS"

## success=TRUE
# uncompressed (compress on the fly) when BITPIX is NOT -32
FITS=$tdata/scrape/20160315/ct4m-arcoiris/SV_f0064.fits
## => 20160322/ct4m/2016A-0612/c4ai_160322_234217_gri_t846000_TADASMOKE.fits.fz
# "fpack -L" should yield: "tiled_rice"
testCommand db2_6b "passdrop $PTO $FITS 20160315 ct4m-arcoiris" "^\#" n 0
#!testLog db2_6b_log "pylogfilter $plog \"$MARKER\" $FITS"

############
### All three (obj_355, obj_355a, obj_355b) have same checksum!!!
### Causes trouble with collisions (on dq, auditdb)
###
## success=FALSE
# Will not have a personality for "bad-instrum" (tele-instrum)
# when monitor needs it.  So fail on MOUNTAIN hence timeout on valley.
FITS=$tdata/short-drop/20160909/bad-instrum/obj_355b.fits.fz
testCommand db2_2 "dropfile $FTO $FITS 20160909 bad-instrum 1" "^\#" n 9
#!testLog db2_2_log "pylogfilter $plog \"$MARKER\" $FITS"

## success=TRUE
FITS=$tdata/short-drop/20141220/wiyn-whirc/obj_355.fits.fz
testCommand db2_3 "passdrop $PTO $FITS 20141220 wiyn-whirc" "^\#" n 0
#!testLog db2_3_log "pylogfilter $plog \"$MARKER\" $FITS"
### 
############

## success=FALSE
FITS=$tdata/short-drop/20160610/kp4m-mosaic3/mos3.badprop.fits
testCommand db2_5 "faildrop $FTO $FITS 20160610 kp4m-mosaic3" "^\#" n 0 
#!testLog db2_5_log "pylogfilter $plog \"$MARKER\" $FITS"

## success=TRUE
# FITS not readable by Astropy, but CFITSIO (fitscopy) will correct it on mtn
FITS="$tdata/noastropy/20161230/soar-goodman/0084.leia.fits"
testCommand db6_1 "passdrop $PTO $FITS 20161230 soar-goodman" "^\#" n 0
#!testLog db6_1_log "pylogfilter $plog \"$MARKER\" $FITS"

## success=TRUE
# This one takes longish! Could not find smaller file that astropy fixes
# (original fails fitsverify, to-be-ingested passes verify)
# 57 seconds to iputr 71,222,400 bytes @ 10mbps
# fail-pass fitsverify
FITS="$tdata/scrape/20160314/kp4m-mosaic3/mos3.75870.fits.fz"
testCommand db1_2 "passdrop 70 $FITS 20160314 kp4m-mosaic3" "^\#" n 0
#!testLog db1_2_log "pylogfilter $plog \"$MARKER\" $FITS"


#########################
# TODO: Summary check. We expect:  !!!
#  3 INFO "SUCCESSFUL submit_to_archive"
#  2 ERROR IngestRejection
#  2 WARNING 
testLog db3_1_log "pylogrun $plog \"$MARKER\""

# Verify behavior on MOUNTAIN!!!
# Should fail at MOUNTAIN (see watch.log)
# Therefore not transfer to valley, so timeout here.
#! FITS=$tdata/short-drop/bad-date/wiyn-whirc/obj_355a.fits.fz
#! testCommand db2_1 "faildrop $FTO $FITS bad-date wiyn-whirc" "^\#" n 9
#! testLog db2_1_log  "pylogfilter $plog \"$MARKER\" $FITS"

rsync -az --password-file ~/.tada/rsync.pwd tada@$MTNHOST::logs ~/.tada/mountain-logs
testLog db4_1_log "mtnlogrun $mtn_plog ${mtn_plog_start}"
testLog db5_1_log "mtnlogrun $mtn_wlog ${mtn_wlog_start}"




##############################################################################
### Check AUDIT and LOG counts


cmd="$tadadir/scripts/check_audit.py --success_True 5 --success_False 1"
testCommand cadb1 "$cmd" "^\#" n 0
echo "Reconsider how many success=true/false audit records to expect!!!"
echo "   (really expect: 5=True, 2=False)"


###########################################
#echo "WARNING: ignoring remainder of tests"
#exit $return_code
###########################################a


# Directory structure is wrong! (one too deep) TEST ON MOUNTAIN
# scrape/<date>/<instrument>/.../*.fits.fz
#! testCommand db2_1 "mdbox $tdata/scrape" "^\#" n
#! testCommand db2_2 "sbox" "^\#" n

# TOO LONG!!! Almost 4 minutes to transfer
#! FITS=$tdata/short-drop/20160610/kp4m-mosaic3/mos3.94567.fits
#! testCommand db2_4 "passdrop 230 $FITS 20160610 kp4m-mosaic3" "^\#" n 0 

###
##############################################################################

ENDMARKER="`date '+%Y-%m-%d %H:%M:%S'` END-SMOKE-TEST"
echo $ENDMARKER >> $plog
echo $ENDMARKER >> /var/log/tada/pop-detail.log

echo "MAX_FOUND_TIME=$MAX_FOUND_TIME"
emins=$((`date +'%s'` - tic))
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
#cd $origdir
popd
#exit $return_code
return $return_cod
