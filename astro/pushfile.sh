#!/bin/bash 
# PURPOSE: Push a filename (with its checksum) to the Transfer queue
#
# EXAMPLE: push-file.sh data/mandelbrot.jpg
#
# AUTHORS: S.Pothier
##############################################################################

echo "Executing: $0"
cmd=`basename $0 .sh`
fullfname=$1

if [ -f "${fullfname}" ]; then
    md5sum ${fullfname} | dqcli -q transfer --push  - 
    msg="Pushed \"${fullfname}\" to xfer Queue."
    #!echo $msg
    logger -i -t $cmd -p local1.info $msg
else
    msg="ERROR: File \"${fullname}\" not found. Not pushing"
    #!echo $msg
    logger -is -t $cmd -p local1.error $msg
    exit 1
fi
