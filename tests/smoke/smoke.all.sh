#!/bin/sh
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in

$SCRIPTDIR/smoke.fits_submit.sh
$SCRIPTDIR/smoke.pipeline_submit.sh
$SCRIPTDIR/smoke.sh
