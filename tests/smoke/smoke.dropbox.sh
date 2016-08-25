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
source dropsub.sh

return_code=0
SMOKEOUT="README-smoke-results.dropbox.txt"
MANIFEST="$dir/manifest.out"
ARCHLOG="/var/log/tada/archived.manifest"
AUDITDB="/var/log/tada/audit.db"

echo "# "
echo "# Starting tests in \"smoke.dropbox.sh\" ..."
echo "# "
source tada-smoke-setup.sh

SRCFILES=""
##############################################################################

tic=`date +'%s'`

testCommand db7_1 "mdbox $tdata/fitsverify/" "^\#" y 0

###########################################
#!echo "WARNING: ignoring remainder of tests"
#!exit $return_code
###########################################a

# - Fail gracefully with bad directory format
# - On-the-fly lossless fpack (even with floating point images)
testCommand db3_1 "mdbox $tdata/short-drop/" "^\#" n 1


#############
## WARNING: combining multiple dropbox tests can result in filename collisions
#! mars_stuff
#! mars_rollback
#
# (even between "different" names such as myfile.fits and myfile.fits.fz)
# The result will depend on timing!  So avoid collisions across tests!
# <date>/<instrument>/.../*.fits.fz
#testCommand db1_1 "mdbox $tdata/scrape/" "^\#" y


emins=$((`date +'%s'` - tic))
# expect about 168 seconds
echo "# Completed dropbox test: " `date` " in $emins seconds"a


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
return $return_cod
