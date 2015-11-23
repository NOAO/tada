#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test; 
# EXAMPLE:
#   ~/sandbox/tada/tests/smoke/smoke.dome.sh
# This file tests raw_post of:
#   1. non-FITS
#   2. compliant FITS with no options (no need for them, so ingest success)
#   3. non-compliant FITS (ingest failure)
#   4. FITS made compliant via passed options (ingest success)
#

cmd=`basename $0`

SCRIPT=$(readlink -f $0)      #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
#tadadir=$(dirname $testdir)
#tdata=$SCRIPTDIR/data
tdata=$SCRIPTDIR/tada-test-data
# tdata=/sandbox/tada/tests/smoke/tada-test-data
echo "tdata=$tdata"

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=~/scripts:$SCRIPTDIR:$PATH

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.txt"

echo ""
echo "Starting tests with: \"$SCRIPT\" ..."
echo ""
echo ""


if [ -d "$tdata/basic" ]; then
    echo "data directory ($tdata/basic) exists. Using it"
else
    echo "data directory ($tdata/basic) does not exist. Transfering it"
    wget http://mirrors.sdm.noao.edu/tada-test-data/fits-test-data.tgz
    tar xf fits-test-data.tgz
fi

# Standard post of file that can be used from any DOME
function rpost () {
    ffile=$1; shift
    pers=""
    for p; do
	    pers="$pers -p $p"
    done
    raw_post $pers $ffile
    status=$?
    if [ $status -eq 0 ]; then
	curl -s -S "http://mars.sdm.noao.edu:8000/provisional/add/$archfile/?source=$ffile"
    else
	echo "FAILED raw_post of $ffile"
    fi
}


#!##########################
#!# 1_1: pass; non-FITS
#!file=$tdata/basic/uofa-mandle.jpg
#!testCommand rp1_1 "rpost $file 2>&1" "^\#" y


##########################
# 2_1: pass ingest without options
file=$tdata/basic/k4k_140922_234607_zri.fits.fz
testCommand rp2_1 "rpost $file 2>&1" "^\#" y


#!##########################
#!# 3_1: fail ingest
#!file=$tdata/basic/kp109391.fits.fz
#!testCommand rp3_1 "rpost $file 2>&1" "^\#" y
#!
#!
#!##########################
#!# 4_1: pass ingest using options
#!file=$tdata/basic/obj_355.fits
#!testCommand rp4_1 "rpost $file 2>&1" "^\#" y

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

