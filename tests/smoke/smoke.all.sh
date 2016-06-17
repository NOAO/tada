#!/bin/sh

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

rm /var/log/tada/pop*.log
touch /var/log/tada/pop.log /var/log/tada/pop-detail.log
chgrp tada /var/log/tada/pop*.log


function tally () {
    mastertotalcnt=$((totalcnt + mastertotalcnt))
    masterfailcnt=$((failcnt + masterfailcnt))
    echo "Score so far; passed=$(($totalcnt-$failcnt))/$totalcnt"
    echo "Score so far; master passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt"
    totalcnt=0
    failcnt=0
}

# Mountain (dome) or Valley
#source $SCRIPTDIR/smoke.sh; tally
#source $SCRIPTDIR/smoke.raw.sh; tally # REMOVED because uses deprecated LP

# Valley
#! $SCRIPTDIR/smoke.fits_compliant.sh; tally
#! $SCRIPTDIR/smoke.fits_submit.sh; tally
#! $SCRIPTDIR/smoke.pipeline_submit.sh; tally

source $SCRIPTDIR/smoke.direct.sh; tally  # test error conditions
#!echo "WARNING: skipping scrape test!!!"
source $SCRIPTDIR/smoke.scrape.sh; tally  # uses direct_submit

source $SCRIPTDIR/smoke.dropbox.sh; tally

echo "tada config params used:"
grep  "get_config got:" /var/log/tada/pop-detail.log | tail -1
echo 
echo "Multi-test score: passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt"
echo "Remember to:"
echo "  1. try Portal to prove stated files can be retrieved!"
echo "  2. verify Archive filenames look ok: http://localhost:8000/provisional/"

emins=$(((`date +'%s'` - tic)/60))
passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt
cat <<EOF | mail -s "Smoke.all completed! (passed=$passed)" pothier@email.noao.edu
Script:   $SCRIPT
Started:  $sdate
Finished: `date`

Multi-test score: passed=$passed
elapsed minutes:  $emins

Remember to:
  1. try Portal to prove stated files can be retrieved!
  2. verify Archive filenames look ok: http://mars.sdm.noao.edu:8000/provisional/
EOF
