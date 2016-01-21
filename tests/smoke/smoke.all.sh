#!/bin/sh

## TO ADD:
##  failure tests; make sure DIRECT ingest failures return non-zero status

SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in

source /sandbox/tada-tools/dev-scripts/irods_init.sh

# Valley
#! $SCRIPTDIR/smoke.fits_compliant.sh
#! $SCRIPTDIR/smoke.fits_submit.sh
#! $SCRIPTDIR/smoke.pipeline_submit.sh
$SCRIPTDIR/smoke.direct.sh
$SCRIPTDIR/smoke.scrape.sh

# Mountain (dome) or Valley
$SCRIPTDIR/smoke.sh
#!$SCRIPTDIR/smoke.raw_post.sh

echo "Remember to:"
echo "  1. try Portal to prove stated files can be retrieved!"
echo "  2. verify Archive filenames look ok: http://localhost:8000/provisional/"



