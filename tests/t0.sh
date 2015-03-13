#!/bin/bash 
# PURPOSE: Submit file to TADA and verify it moved through system ok.

#! Run as: "tada" user
#!if [ "$USER" != "tada" ]; then
#!    echo "Must be run as 'tada' user. Aborting!" 1>&2
#!    exit 1
#!fi


date > $HOME/TEXTFILE.txt

strs=""


# These may be processed asynchronously!
f=$HOME/TEXTFILE.txt
req=`lp -d astro $f`
id=`echo $req | awk '{ print substr($4,7) }'`
base=`basename $f`
echo "Submitted: $id/$base"
strs="$strs $id/$base"

f=/data/raw/nhs_2014_n14_299403.fits
req=`lp -d astro -o _DTCALDAT=2014-09-21 $f`
id=`echo $req | awk '{ print substr($4,7) }'`
base=`basename $f`
echo "Submitted: $id/$base"
strs="$strs $id/$base"


f=/data/bok/bokrm.20140425.0119.fits
req=`lp -d astro $f`
id=`echo $req | awk '{ print substr($4,7) }'`
base=`basename $f`
echo "Submitted: $id/$base"
strs="$strs $id/$base"

echo "strs=$strs"

/sandbox/tada/scripts/finished-files.sh $strs



