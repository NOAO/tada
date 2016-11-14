#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Tests data flow of a bunch of files at once.
#   Requires external data directory.
#

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
SMOKEOUT="$sto/README-smoke-results.txt"

function cleanStart () {
    # Clear old transfer queue
    dqcli --clear -s 

    echo "yes" | sudo $deletemirror > /dev/null
    echo "yes" | sudo $deletenoarch > /dev/null
}

function dqout () {
    (
	sleep 5 # account for REDIS latency
	dqcli --list active
	dqcli --list inactive
	dqcli --list records
	dqcli -s
	) | sed 's|/[0-9]\+/|/|g'
}

##############################################################################

echo ""
echo "Starting tests in \"$dir\" ..."
echo "  (this test runs longer than most)"
echo ""
echo ""

#!wait=50  # seconds to wait for file to make it thru ingest
#!prms="-c -t $wait"

MANIFEST=/var/log/tada/submit.manifest
DATA=/data
SOUT=/tmp/submitted.$$.out
SALL=/tmp/submitted-all.$$.out

optprms="-o __jobid_type=seconds "
fake1="-o _DTCALDAT=2014-09-21"
fake2="-o _PROPID=2014B-0461"
fake3="-o _OBSERVAT=KPNO -o _OBSID=kp4m.20140922T013548 -o _PROPID=2014B-0461"
fake4="-o _DATE-OBS=2014-09-22T01:35:48.0"
fake5="-o _INSTRUME=KOSMOS"


rm -f $SALL > /dev/null
touch $SALL
cleanStart  > /dev/null

postproc -s $SOUT -p fake1 -p fake2 -p fake6 $optprms  \
  $DATA/scraped/mtn_raw/wiyn-bench/24dec_2014.061.fits \
  $DATA/scraped/mtn_raw/wiyn-bench/dark_1800s_091.fits \
  $DATA/scraped/mtn_raw/ct4m-cosmos/Night1.21953.fits    
cat $SOUT >> $SALL

# These are missing DTTELESC, DTTITLE (could provide with "-p fake6")
postproc -s $SOUT -p fake1 -p fake2  $optprms            \
  $DATA/scraped/mtn_raw/wiyn-whirc/obj_355.fits          \
  $DATA/scraped/mtn_raw/soar-soi/LTT1020_6693.072.fits   \
  $DATA/scraped/mtn_raw/ct13m-andicam/ir141225.0179.fits \
  $DATA/scraped/mtn_raw/soar-osiris/SO2014B-015_1215.0188.fits
cat $SOUT >> $SALL


postproc -s $SOUT -p fake1  -o _DTTITLE=wubba  $optprms \
  $DATA/scraped/mtn_raw/kp4m-mosaic_1_1/spw54553.fits \
  $DATA/scraped/mtn_raw/kp4m-mosaic_1_1/n2.54779.fits
cat $SOUT >> $SALL

postproc -s $SOUT -p fake1 -p fake2 -p fake5  $optprms \
  $DATA/scraped/mtn_raw/ct15m-echelle/chi141225.1302.fits
cat $SOUT >> $SALL

postproc -s $SOUT -p fake1 -p fake3 -p fake4  $optprms \
  $DATA/scraped/mtn_raw/kp09m-hdi/c7015t0267b00.fits
cat $SOUT >> $SALL

strs=`cat $SALL`
if finished-files.sh -v 1 -t 120 $strs; then
    echo "All submitted files were accounted for."
else
    echo "Some submitted files were NOT accounted for (in $TIMEOUT seconds)!"
fi

##########################
findout=smoke-2.find
status=smoke-2.status
find /var/tada -type f | sed 's|/[0-9]\+/|/|g' | sort > $findout
testOutput tada1_1 $findout '^\#' n
awk '{ sub(".*/","",$3); print $2, $3, $5 } ' < $MANIFEST > $status
testOutput tada1_2 $status '^\#' n
testCommand tada1_3 "dqcli -s 2>&1" "^\#" n
testCommand tada1_4 "dqcli --list inactive 2>&1" "^\#" n

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

