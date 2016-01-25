#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
#   Use mountain dropbox to ingest set files files. Run from Valley.
#
#   The "dropbox" is a directory that is monitored for fits files appearing
#   in it. Any that appear are submitted for ingest.  

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
SCRIPTDIR=$(dirname $SCRIPT) #Absolute path this script1 is in
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
source mars.sh
source fsub.sh
return_code=0
SMOKEOUT="README-smoke-results.dropbox.txt"

echo ""
echo "Starting tests in \"$SCRIPT\" ..."
echo ""
mars_stuff
mars_rollback
echo ""

if [ -d "$tdata/basic" ]; then
    echo "Data directory ($tdata/basic) exists. Using it!"
else
    echo "data directory ($tdata/basic) does not exist. Transfering it"
    wget -nc http://mirrors.sdm.noao.edu/tada-test-data/fits-test-data.tgz
    tar xf fits-test-data.tgz
fi

# SUCCESSFUL INGEST example:b
# 2016-01-21 23:08:36,742 root            INFO     PASSED submit_to_archive; /var/tada/cache/vagrant/6/obj_355.fits.fz as /noao-tuc-z1/mtn/20141219/WIYN/2012B-0500/kww_141220_130138_ori_3334730996.fits
#
#grep "INFO     PASSED submit_to_archive" /var/log/tada/pop.log 

function dbox () {
    srcdir=$1
    mhost="mountain.`hostname --domain`"
    # Force all fits files to be touched on remote (which creates event)
    find $srcdir -name "*.fits*" -exec touch {} \;
    rsync -avz --password-file ~/.tada/rsync.pwd $srcdir tada@$mhost::dropbox
    finished-files.sh -m /var/log/tada/pop.log 
}

##############################################################################

testCommand db1_1 "dbox $tdata/scrape" "^\#" n 1

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


# Don't move or remove! 
cd $origdir
exit $return_code

