#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Test use of postproc
#
# This file tests submit of:
#   1. non-FITS
#   2. compliant FITS with no options (no need for them, so ingest success)
#   3. non-compliant FITS (ingest failure)
#   4. FITS made compliant via passed options (ingest success)

cmd=`basename $0`

#Absolute path to this script
SCRIPT=$(readlink -e $0)
#Absolute path this script is in
SCRIPTDIR=$(dirname $SCRIPT)
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
smokedata=$SCRIPTDIR/data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

PATH=$tadadir/scripts:$SCRIPTDIR:$PATH
source smoke-lib.sh
return_code=0
SMOKEOUT="$sto/README-smoke-results.txt"
delay=6 # seconds
##############################################################################

echo "smokedata=[$smokedata]"
postproc -v $smokedata/uofa-mandle.jpg
postproc -v -p smoke $smokedata/raw/LTT1020_6606.052.fits
postproc -v -p smoke -o _INSTRUME=chiron $smokedata/raw/chi141225.1238.fits

##########################
# 1_1: pass; non-FITS
#!file=$smokedata/uofa-mandle.jpg
#!testCommand pproc1_1 "postproc -p debug $file 2>&1" "^\#" y
