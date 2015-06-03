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
tdata=$SCRIPTDIR/data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/scripts:$tadadir/dev-scripts:$SCRIPTDIR:$PATH
deletemirror=`type -path delete-mirror.sh`
deletenoarch=`type -path delete-noarchive.sh`

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.txt"
#!delay=7 # seconds
delay=6 # seconds

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

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

wait=50  # seconds to wait for file to make it thru ingest
prms="-v 1 -c -t $wait"
optprms="-o __jobid_type=seconds"
# -o __calchdr=PROPIDtoDT
MANIFEST=/var/log/tada/submit.manifest


##########################
# 1_1: pass; non-FITS
file=$tdata/uofa-mandle.jpg
opt="$optprms "
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada1_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada1_2 $status.clean '^\#' n
testCommand tada1_3 "dqout 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada1_4 $findout '^\#' n


## k4k NOW GETS THIS ERROR:
# tada.exceptions.SubmitException: HTTP response from Archive Ingest: "Failure reason:Failed to ingest file:/noao-tuc-z1/tada/vagrant/2/k4k_140922_234549_zuu_1186823651.hdr error msg:Got more than one observation matching calibration date for proposal. Query: select distinct o from ObservationEntity o join fetch o.proposalSet p where p.proposalId = ?1 and o.calibrationDate between ?2 and ?3 and o.publicDataReleaseDate < ?4"; Operator:: <none>
##

##########################
# 2_1: pass ingest without options
file=$tdata/k4k_140922_234607_zri.fits.fz
opt="$optprms "
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada2_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada2_2 $status.clean '^\#' n
testCommand tada2_3 "dqout 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada2_4 $findout '^\#' y


##########################
# 3_1: fail ingest
file=$tdata/kp109391.fits.fz
opt="$optprms "
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada3_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada3_2 $status.clean '^\#' n
testCommand tada3_3 "dqout 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada3_4 $findout '^\#' n


##########################
# 4_1: pass ingest using options
file=$tdata/ct582021.fits.fz 
opt="$optprms -o _INSTRUME=mosaic -o _DTPROPID=2014B-0461"
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada4_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada4_2 $status.clean '^\#' n
testCommand tada4_3 "dqout 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada4_4 $findout '^\#' n

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
exit $return_code

