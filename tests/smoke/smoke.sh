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

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.txt"


echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""

# Clear old transfer queue
dqcli --clear 

prms="-c -t 15"
MANIFEST=/var/log/tada/submit.manifest

files="$tdata/dont-panic.jpg /data/bok/bokrm.20140425.0119.fits"
stat=no-opt.log
testCommand tada1_1 "tada-submit $prms $files 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $stat.clean
testOutput tada1_2 $stat.clean '^\#' n
#!testCommand tada1_3 "dqcli -s 2>&1" "^\#" n

# lp -d astro -o _DTCALDAT=2014-09-21 /data/raw/nhs_2014_n14_299403.fits
files="/data/raw/nhs_2014_n14_299403.fits"
stat=opt1.log
opt1="-o _DTCALDAT=2014-09-21"
testCommand tada2_1 "tada-submit $opt1 $prms $files 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $stat.clean
testOutput tada2_2 $stat.clean '^\#' n
#!testCommand tada2_3 "dqcli -s 2>&1" "^\#" n

###########################################
#! echo "WARNING: ignoring remainder of tests"
#! exit $return_code
###########################################


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

