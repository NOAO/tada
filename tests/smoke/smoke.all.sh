#!/bin/bash

## TO ADD:
##  failure tests; make sure DIRECT ingest failures return non-zero status

sdate=`date`
tic=`date +'%s'`
export failcnt=0
export totalcnt=0
masterfailcnt=0
mastertotalcnt=0

SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
# SCRIPTDIR=/sandbox/tada/tests/smoke/

#rm /var/log/tada/pop*.log
date > /var/log/tada/pop.log
#!date > /var/log/tada/pop-detail.log
#!chgrp tada /var/log/tada/pop*.log


function tally () {
    src=$1
    mastertotalcnt=$((totalcnt + mastertotalcnt))
    masterfailcnt=$((failcnt + masterfailcnt))
    echo "Score so far; suite  passed=$(($totalcnt-$failcnt))/$totalcnt ($src)"
    echo "Score so far; master passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt"
    totalcnt=0
    failcnt=0
}


##############################################################################
### Context of tests
###
echo "# Running: $SCRIPT"
echo "Current User: $USER"
echo "Hiera values:"
cat /etc/tada/hiera.yaml

pushd $SCRIPTDIR > /dev/null 2>&1
echo -n "TADA repo branch/tag currently active: "
# --short option not available in git 1.7.1
#!git symbolic-ref --short -q HEAD || git describe --tags --exact-match
git symbolic-ref -q HEAD || git describe --tags --exact-match
popd > /dev/null 2>&1
####
##############################################################################

echo "# "
echo "# Starting tests in \"smoke.all.sh\"  [allow 17 minutes on chimp] ..."
echo "# "

####
# Make sure hosts and services are running!
source $SCRIPTDIR/smoke.system.sh
tally smoke.system

####
# Test Valley only behavior
#! $SCRIPTDIR/smoke.fits_compliant.sh; tally
#! $SCRIPTDIR/smoke.fits_submit.sh; tally
source $SCRIPTDIR/smoke.direct.sh; tally   smoke.direct # test error conditions
source $SCRIPTDIR/smoke.scrape.sh; tally   smoke.scrape # uses direct_submit
source $SCRIPTDIR/smoke.pipeline.sh; tally smoke.pipeline

####
# Mountain (dome) or Valley
#!source $SCRIPTDIR/smoke.raw.sh; tally raw# REMOVED because uses deprecated LP
source $SCRIPTDIR/smoke.dropbox.sh; tally smoke.dropbox



##############################################################################

echo "tada config params used:"
grep  "get_config got:" /var/log/tada/pop-detail.log | tail -1
echo 
echo "Multi-test score: passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt"
echo "Remember to:"
echo "  1. try Portal to prove stated files can be retrieved!"
echo "  2. verify Archive filenames look ok: http://localhost:8000/provisional/"

emins=$(((`date +'%s'` - tic)/60))
passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt
hostname=`hostname`
cat <<EOF | mail -s "Smoke.all completed! (passed=$passed)" pothier@email.noao.edu
Script:   $hostname:$SCRIPT
Started:  $sdate
Finished: `date`

Multi-test score: passed=$passed
elapsed minutes:  $emins

Remember to:
  1. try Portal to prove stated files can be retrieved!
  2. verify Archive filenames look ok: http://mars.sdm.noao.edu:8000/provisional/
EOF
