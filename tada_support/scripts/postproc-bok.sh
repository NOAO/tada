#!/bin/bash
# PURPOSE: Use postproc to ingest all BOK fits files.
#

#!bokdir=${1:-/data/bok-real} # 828 files
#!bokdir=${1:-/data/bok2/20150415} # 30 files

#bdir="/data/bok2/20150415 /data/bok2/20150416"

bokdir=${1:-/data/bok2}  # 3786 files
#!boklist=/sandbox/tada/scripts/bok2.list
boklist=/sandbox/tada/scripts/bok/bok2.do

function abort {
    echo "ABORT of postproc-bok.sh"
    exit 1
}
trap abort ERR SIGINT SIGTERM

date

#! optprms="-o __jobid_type=seconds "  # don't fail ingest on dupes
#! find $bokdir -name "*.fits.fz" -print0 \
#!     | xargs -0 -L 1 postproc -p bok $optprms


#for fits in `find $bokdir -name "*.fits.fz" -print`; do
for fits in `grep  -v \# $boklist`; do
    echo "submit: $fits"
    postproc -v -p bok $fits
    if [ -f /etc/tada/pause ]; then
	# sleep 12
	# sleep 8
	source /etc/tada/pause  # trick to pause more or abort (exit)
    fi

    # stop ingest errors from causing disk to fill up!!!
    #!dqcli --clear 
    #!rm -rf /var/tada/mountain-mirror/vagrant
done

date
sleep 5
dqcli -s
ils -r -l /noao-tuc-z1/tada/

echo "Remember to check results through portal:"
echo "   http://portal-pat-sdm.noao.edu/  -OR-"
echo "   http://portal-nvo.noao.edu/"
SUMMARY=/tmp/postproc-bok.summary
cat <<EOF > $SUMMARY
When: `date`

Queue: 
`dqcli -s`

IRODS:
`ils -r -l /noao-tuc-z1/tada/`
EOF

