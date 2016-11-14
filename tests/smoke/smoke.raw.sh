#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test; 
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.sh
# This file tests submit of:
#   1. non-FITS
#   2. compliant FITS with no options (no need for them, so ingest success)
#   3. non-compliant FITS (ingest failure)
#   4. FITS made compliant via passed options (ingest success)
#
# TODO:
#  - check BOTH Valley and Mountain.  All submitted files accounted for?
#  - Logged errors sent via email?
#  - failure modes;
#    + no connection between mountain/valley
#    + out of disk space (Mountain, Valley)
#    + valley:rsyncd down

cmd=`basename $0`

#Absolute path to this script
SCRIPT=$(readlink -e $0)
#Absolute path this script is in
SCRIPTDIR=$(dirname $SCRIPT)
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
#tdata=$SCRIPTDIR/data
tdata=$SCRIPTDIR/tada-test-data/basic
# tdata=/sandbox/tada/tests/smoke/tada-test-data/basic


dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/../tada-cli/scripts:$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH
deletemirror=`type -path delete-mirror.sh`
deletenoarch=`type -path delete-noarchive.sh`

source smoke-lib.sh

return_code=0
SMOKEOUT="$sto/README-smoke-results.raw.txt"
#!delay=7 # seconds
delay=6 # seconds

MIRROR=/var/tada/cache
NOARCHIVE=/var/tada/anticache


function cleanStart () {
    # Clear old transfer queue
    dqcli --clear -s 

    echo "yes" | sudo $deletemirror > /dev/null
    echo "yes" | sudo $deletenoarch > /dev/null
}

function dqout () {
    (
	sleep $delay # account for possible REDIS latency
	dqcli --list active
	dqcli --list inactive
	dqcli --list records
	dqcli -s
	) | sed 's|/[0-9]\+/|/|g'
}

echo "# "
echo "# Starting tests in \"smoke.raw.sh\" ..."
echo "# "
source tada-smoke-setup.sh

wait=50  # seconds to wait for file to make it thru ingest
prms="-v 1 -c -t $wait"
optprms="-o __jobid_type=seconds"
# -o __calchdr=PROPIDtoDT
MANIFEST=/var/log/tada/submit.manifest


##
## Tired of messing with non-FITS file.  No requirement to handle it anyhow!
##
#!##########################
#!# 1_1: pass; non-FITS
#!file=$tdata/uofa-mandle.jpg
#!opt="$optprms "
#!status=`basename $file`.status
#!findout=find-`basename $file`.out
#!cleanStart  > /dev/null
#!testCommand tada1_1 "tada-submit $opt $prms $file 2>&1" "^\#" n
#!awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
#!testOutput tada1_2 $status.clean '^\#' n
#!testCommand tada1_3 "dqout 2>&1" "^\#" n
#!find $MIRROR $NOARCHIVE -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
#!testOutput tada1_4 $findout '^\#' n


##########################
# 2_1: pass ingest without options
file="$tdata/cleaned-bok.fits.fz"
opt="$optprms "
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada2_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada2_2 $status.clean '^\#' n
testCommand tada2_3 "dqout 2>&1" "^\#" n
find $MIRROR $NOARCHIVE -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada2_4 $findout '^\#' n


##########################
# 3_1: fail ingest
file=$tdata/kp109391.fits.fz
opt="$optprms "
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada3_1 "tada-submit $opt $prms $file 2>&1" "^\#" n
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada3_2 $status.clean '^\#' n
testCommand tada3_3 "dqout 2>&1" "^\#" n
find $MIRROR $NOARCHIVE -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada3_4 $findout '^\#' n


##########################
# 4_1: pass ingest using options
file=$tdata/obj_355.fits
# (Personality = wiyn-whirc)
opt="$optprms \
 -o __calchdr=PROPIDplusCentury,IMAGTYPEtoOBSTYPE,DTCALDATfromDATEOBStus \
 -o _DTTELESC=WIYN \
 -o _DTINSTRU=whirc \
 -o _DTSITE=kp \
 -o _PROCTYPE=raw \
 -o _PRODTYPE=image \
 -o __filename=$file \
"
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada4_1 "tada-submit $opt $prms $file 2>&1" "^\#" n
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada4_2 $status.clean '^\#' n
testCommand tada4_3 "dqout 2>&1" "^\#" n
find $MIRROR $NOARCHIVE -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada4_4 $findout '^\#' n

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a


##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
    echo "#"
    echo "ALL $totalcnt smoke tests PASSED ($SMOKEOUT created)"
    echo "All $totalcnt tests passed on " `date` > $SMOKEOUT
else
    echo "Smoke FAILED $failcnt/$totalcnt (no $SMOKEOUT produced)"
fi


# Don't move or remove! 
cd $origdir
#exit $return_code          #if EXECUTED
#return $return_code        #if SOURCED
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return $return_code
else
    exit $return_code
fi
