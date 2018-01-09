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
tdata=/data/tada-test-data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH

#! source /opt/tada/venv/bin/activate

source smoke-lib.sh
return_code=0

SMOKEOUT="$sto/README-smoke-results.direct.txt"

echo "# "
echo "# Starting tests in \"smoke.direct.sh\"  [allow 4 minutes] ..."
echo "# "
source tada-smoke-setup.sh




##############################################################################

# Clear MARS log in preparation for counting WARNINGS and ERRORS
curl "http://$MARSHOST:8000/audit/marsclearlog/" > /dev/null 2>&1
curl "http://$MARSHOST:8000/audit/hideall/"      > /dev/null 2>&1
echo "Cleared MARS log and HIDE-ALL audit records"

###########################################
###
#!rm $SMOKEOUT 2>/dev/null
#!if [ $return_code -eq 0 ]; then
#!    echo ""
#!    echo "ALL $totalcnt smoke tests PASSED ($SMOKEOUT created)"
#!    echo "All $totalcnt tests passed on " `date` > $SMOKEOUT
#!else
#!    echo "Smoke FAILED $failcnt/$totalcnt (no $SMOKEOUT produced)"
#!fi
#!
#!echo "WARNING: ignoring remainder of tests *************************"
#!exit $return_code
###
###########################################



#############################################
### High Level Science Products (HLSP) submit
### /noao-tuc-z1/hlsp/smoketest/jira/tada-2/clean-bok-TADASMOKE.fits.fz
###
fits="$tdata/basic/cleaned-bok.fits.fz"
#testCommand hs2_1 "hsub smoketest/jira/tada-2 $fits" "^\#" y
testCommand hs2_1 "hsub smoketest/jira/tada-2/clean-bok-TADASMOKE.fits.fz $fits" "^\#" n

################################
## Insure irods (massstore) cleaned up if call to Ingest returns success is false
HDR="/noao-tuc-z1/mtn/20160322/bok23m/1815A-0801/ksb_160322_234217_gri_846000_TADASMOKE.hdr"
testIrods fs7a_1a_irods $HDR
fits="$tdata/scrape/20160315/ct4m-arcoiris/SV_f0064.fits"
newfits=/tmp/changed.fits.fz
# expect failure because 1815A-0801 not in DB
#change_fits $fits $newfits $tdata/basic/change.yaml 
$tadadir/tada/change_hdr.py $fits $newfits $tdata/basic/change.yaml 
testCommand fs7a_1 "fsub $newfits ops-fakearcoiris" "^\#" n 2
testIrods fs7a_1b_irods $HDR
# invoke TIMEOUT on connection to Ingest Service
## FAILED: /tmp/changed.fits.fz not archived; Problem in opening or reading connection to: http://nsaserver.pat.sdm.noao.edu:9000/{'hdrUri': 'irods:///noao-tuc-z1/mtn/20160322/bok23m/1815A-0801/ksb_160322_234217_gri_t846000_TADASMOKE.hdr'}; ('Connection aborted.', BlockingIOError(115, 'Operation now in progress'))
zero_archive_timeout
testCommand fs7a_2 "fsub $newfits ops-fakearcoiris" "^\#" n 2
restore_archive_timeout
testIrods fs7a_1b_irods $HDR
#!rm $newfits

###########################################
### FITS Compliant (fcom)
###
## bad DATE-OBS content
testCommand fc1_1 "fcom $tdata/basic/kp109391.fits.fz" "^\#" n 0
# compliant
testCommand fc2_1 "fcom $tdata/basic/kptest.fits" "^\#" n
###########################################

###########################################
### FITS Submit (fsub)
###
#!# fpack on the fly
#!unpacked="$tdata/scrape/20160314/kp4m-mosaic3/mos3.75675.fits  kp4m-mosaic3"
#!testCommand fs0_1 "fsub $unpacked" "^\#" n

## success does not apply (FALSE)
## non-FITS; (reject, not try to ingest)
testCommand fs1_1 "fsub $tdata/basic/uofa-mandle.jpg" "^\#" n 1


## success=TRUE
## compliant FITS with no options (no need for them, so ingest success)
file2="$tdata/basic/cleaned-bok.fits.fz"
testCommand fs2_1 "fsub $file2" "^\#" n

## success=FALSE
## compliant FITS with no options (BUT, already inserted above so ingest FAIL)
testCommand fs2b_1 "fsub $file2" "^\#" n 2


## success=FALSE
## bad format for DATE-OBS
testCommand fs3_1 "fsub $tdata/basic/kp109391.fits.fz" "^\#"  n 1

## success=TRUE
## FITS made compliant via passed personality options; compress on-the-fly
## (ingest success)
# DATE-OBS= '2014-12-20T13:01:38.0' 
testCommand fs4_1 "fsub $tdata/basic/obj_355.fits wiyn-whirc" "^\#" n

## success=TRUE
## FITS made compliant via passed personality options; multi-extensions
## (ingest success)
testCommand fs5_1 "fsub $tdata/basic/obj_355.fits.fz wiyn-whirc" "^\#" n

## success=FALSE
## non-compliant FITS, missing RAW (ingest failure)
testCommand fs6_1 "fsub $tdata/basic/kptest.fits" "^\#" n 1

## success=FALSE
# New instrument <2016-03-17 Thu>
testCommand fs7_1 "fsub $tdata/scrape/20160315/ct4m-arcoiris/SV_f0064.fits ct4m-arcoiris" "^\#" n

## success=TRUE
# WAS Bad propid; Now Schedule trumps on non-split so is ok.
testCommand fs8_1 "fsub $tdata/broken/20160203/kp4m-newfirm/nhs_1.fits.fz" "^\#"e n

## success=FALSE
# FITS header is missing required metadata fields (PROCTYPE, PRODTYPE)
testCommand fs9_1 "fsub $tdata/broken/20160203/kp/kptest.fits.fz" "^\#" n 1

## success=FALSE
# Modify to fail due to PROPID mismatch with schedule
fits=$tdata/scrape/20160314/kp4m-mosaic3/mos3.75870.fits.fz
newfits=/tmp/changed2.fits.fz
$tadadir/tada/change_hdus.py $fits $newfits $tdata/change_propid.yaml > /dev/null 2>&1
# /schedule/dbpropid/kp4m/mosaic3/2001-01-01/2016A-0453/
# To test, slot should contain list that does NOT include 2016A-0453
testCommand fs10_1  "fsub $newfits" "^\#" n 1


##############################################################################
### Check AUDIT and LOG counts

#!cmd="$tadadir/scripts/check_audit.py --success_True 0 --success_False 1"
#!testCommand ca01 "$cmd" "^\#" n 0
#!cmd="$tadadir/scripts/check_log.py --ERROR 0 --WARNING 0"
#!testCommand ca02 "$cmd" "^\#" n 0

# 11 fsub (same number of audit records)
cmd="$tadadir/scripts/check_audit.py --success_True 4 --success_False 6"
testCommand ca1 "$cmd" "^\#" n 0
echo "Reconsider how many success=true/false audit records to expect!!!"
echo "   (really expect: 4=True, 6=False)"
#! echo "WARNING: did NOT verify AUDIT success=True/False counts!!!"

## There are still lots of errors in mars log
#! cmd="$tadadir/scripts/check_log.py --ERROR 0 --WARNING 0"
#! testCommand ca2 "$cmd" "^\#" n 0




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

