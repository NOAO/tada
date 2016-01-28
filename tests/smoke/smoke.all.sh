#!/bin/sh

## TO ADD:
##  failure tests; make sure DIRECT ingest failures return non-zero status

sdate=`date`
masterfailcnt=0
mastertotalcnt=0

SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in

source /sandbox/tada-tools/dev-scripts/irods_init.sh

function tally () {
    mastertotalcnt=$((totalcnt + mastertotalcnt))
    masterfailcnt=$((failcnt + masterfailcnt))
}

# Mountain (dome) or Valley
$SCRIPTDIR/smoke.sh; tally
#!$SCRIPTDIR/smoke.raw_post.sh
$SCRIPTDIR/smoke.dropbox.sh; tally

# Valley
#! $SCRIPTDIR/smoke.fits_compliant.sh
#! $SCRIPTDIR/smoke.fits_submit.sh
#! $SCRIPTDIR/smoke.pipeline_submit.sh
$SCRIPTDIR/smoke.direct.sh; tally
$SCRIPTDIR/smoke.scrape.sh; tally

echo "Remember to:"
echo "  1. try Portal to prove stated files can be retrieved!"
echo "  2. verify Archive filenames look ok: http://localhost:8000/provisional/"


cat <<EOF | mail -s "Smoke.all completed!" pothier@email.noao.edu
Scripot:  $SCRIPT
Started:  $sdate
Finished: `date`

Multi-test score: passed=$(($mastertotalcnt-$masterfailcnt))/$mastertotalcnt

Remember to:
  1. try Portal to prove stated files can be retrieved!
  2. verify Archive filenames look ok: http://localhost:8000/provisional/
EOF



