#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
#   Use mountain dropbox to ingest set files files. Run from Valley.
#
#   The "dropbox" is a directory that is monitored for fits files appearing
#   in it. Any that appear are submitted for ingest.  

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script is in
testdir=$(dirname $SCRIPTDIR)
tadadir=$(dirname $testdir)
# tadadir=/sandbox/tada
tdata=$SCRIPTDIR/tada-test-data
# tdata=/sandbox/tada/tests/smoke/tada-test-data

dir=$SCRIPTDIR
origdir=`pwd`
cd $dir

export PATH=$tadadir/../tada-tools/dev-scripts:$SCRIPTDIR:$PATH
export PATH=$tadadir/../tada-cli/scripts:$PATH

source smoke-lib.sh

return_code=0
SMOKEOUT="README-smoke-results.dropbox.txt"
MANIFEST="$dir/manifest.out"
ARCHLOG="/var/log/tada/archived.manifest"

function clean_manifest () {
    rm  $MANIFEST > /dev/null
    touch $MANIFEST
    date > $ARCHLOG
    chgrp tada $ARCHLOG
}



echo "# "
echo "# Starting tests in \"smoke.dropbox.sh\" ..."
echo "# "
source tada-smoke-setup.sh


function sbox () {
    mtnhost="mountain.`hostname --domain`"
    statusdir="$SCRIPTDIR/remote_status"
    mkdir -p $statusdir
    rsync -a --password-file ~/.tada/rsync.pwd tada@$mtnhost::statusbox $statusdir
    find $mydir -type f
}

# Mountain Drop BOX
function mdbox () {
    clean_manifest
    srcdir=$1
    MAXRUNTIME=240  # max seconds to wait for all files to be submitted
    boxhost="mountain.`hostname --domain`"
    for f in `find $srcdir \( -name "*.fits" -o -name "*.fits.fz" \)`; do
        # Force all fits files to be touched on remote (which creates event)
        add_test_personality.sh $f
        touch $f
        #echo "SUCCESSFUL submit_to_archive; $f" >> $MANIFEST
        echo "$f" >> $MANIFEST
    done
    echo "# List of files submitted is in: $MANIFEST"
    #rsync -aiz --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    rsync -az  --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    # INFO     SUCCESSFUL submit; /var/tada/cache/20141224/kp09m-hdi/c7015t0267b00.fits.fz as /noao-tuc-z1/mtn/20141223/kp09m/2014B-0711/k09h_141224_115224_zri_TADASMOKE,.fits.fz,
    echo -n "# Waiting up to $MAXRUNTIME secs for all files to be submitted..." 
    finished-log.sh -t $MAXRUNTIME -l $ARCHLOG $MANIFEST
}

# Valley Drop BOX
function vdbox () {
    clean_manifest
    srcdir=$1
    MAXRUNTIME=90  # max seconds to wait for all files to be submitted
    boxhost="valley.`hostname --domain`"
    for f in `find $srcdir \( -name "*.fits" -o -name "*.fits.fz" \)`; do
        # Force all fits files to be touched on remote (which creates event)
        add_test_personality.sh $f
        touch $f
        #echo "SUCCESSFUL submit_to_archive; $f" >> $MANIFEST
        echo "$f" >> $MANIFEST
    done
    echo "# List of files submitted is in: $MANIFEST"
    rsync -az --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    echo -n "# Waiting up to $MAXRUNTIME secs for all files to be submitted..." 
    finished-log.sh -t $MAXRUNTIME -l $ARCHLOG $MANIFEST
}

##############################################################################

tic=`date +'%s'`

# - Fail gracefully with bad directory format
# - OTF lossless fpack (even with floating point images)
testCommand db3_1 "vdbox $tdata/short-drop/" "^\#" n 1

mars_stuff
mars_rollback

# <date>/<instrument>/.../*.fits.fz
testCommand db1_1 "mdbox $tdata/scrape/" "^\#" y
emins=$((`date +'%s'` - tic))
# expect about 168 seconds
echo "# Completed dropbox test: " `date` " in $emins seconds"


# Directory structure is wrong! (one too deep)
# scrape/<date>/<instrument>/.../*.fits.fz
#! testCommand db2_1 "mdbox $tdata/scrape" "^\#" n
#! testCommand db2_2 "sbox" "^\#" n



###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a


##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
    echo ""
    echo "ALL $totalcnt smoke tests PASSED ($SMOKEOUT created)"
    echo "All $totalcnt tests passed on " `date` > $SMOKEOUT
else
    echo "Smoke FAILED $failcnt/$totalcnt (no $SMOKEOUT produced)"
fi

##############################################################################
# Don't move or remove! 
cd $origdir
#exit $return_code
return $return_code
