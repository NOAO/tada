#!/bin/bash -e

cmd=`basename $0`

#Absolute path to this script
SCRIPT=$(readlink -e $0)
#Absolute path this script is in
SCRIPTDIR=$(dirname $SCRIPT)
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)

data=$testdir/data

PATH=$tadadir/scripts:$SCRIPTDIR:$PATH

opt="-t 15"

tada-submit $opt -r nofits.log $data/text-file.txt 
tada-submit $opt -r fits-good.log -o _DTCALDAT=2014-09-21 /data/raw/nhs_2014_n14_299403.fits
tada-submit $opt -r fits-bad.log /data/bok/bokrm.20140425.0119.fits

