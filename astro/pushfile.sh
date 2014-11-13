#!/bin/bash --verbose
# Time-stamp: <11-13-2014 12:36:41 pothiers /home/pothiers/sandbox/tada/astro/pushfile.sh>
#
# PURPOSE: Push a filename (with its checksum) to the Transfer queue
#
# EXAMPLE: push-file.sh sandbox/data-queue/mandelbrot.jpg
#
# AUTHORS: S.Pothier
##############################################################################

echo "Executing: $0"
fullfname=$1

if [ -f "${fullfname}" ]; then
    echo "Pushing \"${fullfname}\" to xfer Queue."
    md5sum ${fullfname} | dqcli --push - 
    echo "Pushed"
else
    echo "ERROR: File \"${fullname}\" not found. Not pushing" 1>&2
    exit 1
fi
