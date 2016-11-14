#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Test remediation work-flow.
#   1. Add missing fields (file NOT previously ingested, on Inactive queue)
#   2. change propid (file prev ingested with WRONG propid)


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
SMOKEOUT="$sto/README-smoke-results.remed.txt"
MANIFEST="$dir/manifest.out"
rm  $MANIFEST > /dev/null
touch $MANIFEST
MAXRUNTIME=210  # max seconds to wait for all files to be submitted
touch /var/log/tada/archived.manifest
chgrp tada /var/log/tada/archived.manifest

echo "# "
echo "# Starting tests in \"smoke.remed.sh\" ..."
echo "# "
source tada-smoke-setup.sh


#!function sbox () {
#!    mtnhost="mountain.`hostname --domain`"
#!    statusdir="$SCRIPTDIR/remote_status"
#!    mkdir -p $statusdir
#!    rsync -a --password-file ~/.tada/rsync.pwd tada@$mtnhost::statusbox $statusdir
#!    find $mydir -type f
#!}
#!
#!function dbox () {
#!    srcdir=$1
#!    mtnhost="mountain.`hostname --domain`"
#!    for f in `find $srcdir \( -name "*.fits" -o -name "*.fits.fz" \)`; do
#!        # Force all fits files to be touched on remote (which creates event)
#!        touch $f
#!        add_test_personality.sh $f
#!        #echo "SUCCESSFUL submit_to_archive; $f" >> $MANIFEST
#!        echo "$f" >> $MANIFEST
#!    done
#!    echo "# List of files submitted is in: $MANIFEST"
#!    rsync -az --password-file ~/.tada/rsync.pwd $srcdir tada@$mtnhost::dropbox
#!
#!    # Failed to submit /var/tada/cache/20160203/kp/kptest.fits.fz
#!
#!    #!echo -n "#Waiting for $MAXRUNTIME seconds for all files to be submitted..." 
#!    #!sleep $((MAXRUNTIME/2))
#!    #!echo -n "half done..."
#!    #!finished-log.sh -l /var/log/tada/archived.manifest $MANIFEST
#!    #!sleep $((MAXRUNTIME/2))
#!    #!echo "#done waiting"
#!    #!finished-log.sh -l /var/log/tada/archived.manifest $MANIFEST
#!}

##############################################################################

# <date>/<instrument>/.../*.fits.fz

# "missing required metadata fields (PROCTYPE, PRODTYPE)"
testCommand dart1_1 "fsub $tdata/broken/20160203/kp/kptest.fits.fz" "^\#" n 1

fits=$tdata/broken/20160203/kp4m-newfirm/nhs_1.fits.fz
personalities="-p $tdata/broken/20160203/kp4m-newfirm/nhs_1.fits.fz.yaml\
  -p /var/tada/personalities/ops/smoke.yaml"
testCommand dart2_1 "direct_submit --loglevel DEBUG $personalities $fits" "^\#" y 1



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
#exit $return_code
return $return_code
