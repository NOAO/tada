#!/bin/bash
# PURPOSE: Use postproc to ingest all BOK fits files.
#

bokdir=${1:-/data/bok-real}
date

#! optprms="-o __jobid_type=seconds "  # don't fail ingest on dupes
#! find $bokdir -name "*.fits.fz" -print0 \
#!     | xargs -0 -L 1 postproc -p bok $optprms

for fits in `find $bokdir -name "*.fits.fz" -print`; do
    postproc -v -p bok $fits

    sleep 7  # Just so my little VM doesn't run out disk space!

    # stop ingest errors from causing disk to fill up!!!
    #!dqcli --clear 
    #!rm -rf /var/tada/mountain-mirror/vagrant
done

date
sleep 5
dqcli -s
ils -r -l /noao-tuc-z1/tada/

echo "Remember to check results through portal: http://portal-pat-sdm.noao.edu/"
