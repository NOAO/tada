#!/bin/sh
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in


# Valley
$SCRIPTDIR/smoke.fits_compliant.sh
$SCRIPTDIR/smoke.fits_submit.sh
$SCRIPTDIR/smoke.pipeline_submit.sh

# Mountain (dome)
$SCRIPTDIR/smoke.sh
$SCRIPTDIR/smoke.raw_post.sh
