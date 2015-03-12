#!/bin/bash 
# PURPOSE: Submit file to TADA and verify it moved through system ok.

#! Run as: "tada" user
#!if [ "$USER" != "tada" ]; then
#!    echo "Must be run as 'tada' user. Aborting!" 1>&2
#!    exit 1
#!fi

log=/var/log/tada/pop.log

echo "BEGIN TEST: $0" > $log


date > ~/BEGIN.txt
date > ~/END.txt

# These may be processed asynchronously!
lp -d astro ~/BEGIN.txt
lp -d astro -o _DTCALDAT=2014-09-21 /data/raw/nhs_2014_n14_299403.fits
lp -d astro /data/raw/nhs_2014_n14_299403.fits


cat /var/log/tada/submit.log
