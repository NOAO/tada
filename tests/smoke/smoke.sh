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


#! testCommand conrules1_1 "conrules -p ../python -m jungle-objects.xml jungle.lpc.gz conrules_out.1.lpc.gz 2>&1" "^\#" n
#! lpc_cat conrules_out.1.lpc.gz > conrules_out.1.lpc.xml
#! testOutput  conrules1_2 conrules_out.lpc.xml "^\#" n


# Clear old transfer queue
dqcli --clear 

prms="-t 15"
files="$tdata/dont-panic.jpg /data/bok/bokrm.20140425.0119.fits"
manifest=no-opt.log
testCommand tada1_1 "tada-submit $prms -r $manifest $files 2>&1" "^\#" y
#!awk '{ print $2, $3, $5 } ' < $manifest > $manifest.clean
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $manifest > $manifest.clean
testOutput tada1_2 $manifest.clean '^\#' n

files="/data/raw/nhs_2014_n14_299403.fits"
manifest=opt1.log
opt1="-o _DTCALDAT=2014-09-21"
testCommand tada2_1 "tada-submit $prms -r $manifest $files 2>&1" "^\#" y
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $manifest > $manifest.clean
testOutput tada2_2 $manifest.clean '^\#' n


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

