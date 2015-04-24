#!/bin/bash
infile=$1
echo "Pushing to submit queue: $infile"
base=`basename $infile`
outfile=/var/tada/mountain-mirror/tada/$base

today=`date '+%Y-%m-%d'`
now=`date '+%Y%m%d%H%M%S%N'`
optfile=$outfile.options
echo "_OBSERVAT=Steward _OBSID=${now} _PROPID=2014B-0461 _DTCALDAT=$today _DTTITLE=wubba _OBSTYPE=object _PROCTYPE=Raw _PRODTYPE=Image" > $optfile


cp $infile $outfile
chmod a+rw $outfile
md5sum $outfile | dqcli --push -

# When running under small vagrant VM.
seconds=7
#!echo "Wait $seconds seconds to avoid filling disk"
df -h .
sleep $seconds
