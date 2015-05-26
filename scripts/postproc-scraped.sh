#!/bin/bash
# PURPOSE: Use postproc to ingest all scraped FITS files.
#

scrapeddir=${1:-/data/scraped/mtn_raw} # 89 files
#maxpersubdir=1
maxpersubdir=1

# NO GOOD
#! ct13m-andicam \   # missing PROPID
#! wiyn-whirc \      # bad PROPID
#! kp09m-hdi \       # missing PROPID

SUBDIRS="\
ct15m-echelle \
ct1m-y4kcam \
ct4m-cosmos \
ct4m-ispi \
kp4m-mosaic_1_1 \
kp4m-newfirm \
soar-goodman \
soar-osiris \
soar-sami \
soar-soi \
soaric7s-soar \
wiyn-bench \
"

# GOOD enough


date

optprms="-o __jobid_type=seconds "  # don't fail ingest on dupes

dqcli --clear
for subdir in $SUBDIRS; do
    fitsdir="$scrapeddir/$subdir"
    echo "Processing FITS files in: $fitsdir"
    #pers=`echo $subdir | cut -f2 -d-`
    pers=$subdir

    fitscnt=0
    for fits in `find $fitsdir -name "*.fits" -print`; do
	fitscnt=$((fitscnt + 1))
	if [ $fitscnt -gt $maxpersubdir ]; then
	    echo "Ignoring remaining FITS files in: $subdir"
	    break
	fi
	#!echo "fitscnt=$fitscnt"
	postproc -v -p $pers -p debug  $fits
	#! sleep 7  # Just so my little VM doesn't run out disk space!
    done
done

date
sleep 5
dqcli -s
ils -r -l /noao-tuc-z1/tada/

echo "Remember to check results through portal: http://portal-pat-sdm.noao.edu/"

SUMMARY=/tmp/postproc-scraped.summary
cat <<EOF > $SUMMARY
When: `date`

Queue: 
`dqcli -s`

IRODS:
`ils -r -l /noao-tuc-z1/tada/`
EOF

