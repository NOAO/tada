#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.sh
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

PATH=$tadadir/scripts:$SCRIPTDIR:$PATH
deletemirror=`type -path delete-mirror.sh`
deletenoarch=`type -path delete-noarchive.sh`

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.txt"

function cleanStart () {
    # Clear old transfer queue
    dqcli --clear -s 

    echo "yes" | sudo $deletemirror > /dev/null
    echo "yes" | sudo $deletenoarch > /dev/null
}

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

wait=50  # seconds to wait for file to make it thru ingest
prms="-c -t $wait"
MANIFEST=/var/log/tada/submit.manifest


##########################
# 1_1: pass; non-FITS
file=/data/other/uofa-mandle.jpg
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada1_1 "tada-submit $prms $file 2>&1" "^\#" y
#! echo "MANIFEST:"; cat /var/log/tada/submit.manifest
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada1_2 $status.clean '^\#' n
testCommand tada1_3 "dqcli -s 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada1_4 $findout '^\#' n

##########################
# 2_1: pass ingest using options
# lp -d astro -o _DTCALDAT=2014-09-21 /data/raw/nhs_2014_n14_299403.fitse
file=/data/raw/nhs_2014_n14_299403.fits
opt="-o _DTCALDAT=2014-09-21"
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada2_1 "tada-submit $opt $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada2_2 $status.clean '^\#' n
testCommand tada2_3 "dqcli -s 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada2_4 $findout '^\#' n


##########################
# 3_1: fail ingest
file=/data/bok/bokrm.20140425.0119.fits
status=`basename $file`.status
findout=find-`basename $file`.out
cleanStart  > /dev/null
testCommand tada3_1 "tada-submit $prms $file 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status.clean
testOutput tada3_2 $status.clean '^\#' n
testCommand tada3_3 "dqcli -s 2>&1" "^\#" n
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada3_4 $findout '^\#' n


###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a


##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
  echo ""
  echo "ALL smoke tests PASSED ($SMOKEOUT created)"
  echo "All tests passed on " `date` > $SMOKEOUT
else
  echo "Smoke FAILED (no $SMOKEOUT produced)"
fi


# Don't move or remove! 
cd $origdir
exit $return_code

