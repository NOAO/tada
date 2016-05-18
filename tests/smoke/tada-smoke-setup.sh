#
# Common setup for running TADA smoke tests.
# Clears database of specially named files, loads test files if needed.
#

#! echo "# Common setup for TADA smoke tests"
source fsub.sh
source mars.sh
mars_stuff
mars_rollback

if [ -d "$tdata" ]; then
    echo "# Data directory ($tdata) exists. Using it!"
else
    echo "# Data directory ($tdata) does not exist. Transfering it"
    #rm /sandbox/tada/tests/smoke/fits-test-data.tgz
    rm $SCRIPTDIR/fits-test-data.tgz
    wget -nc http://mirrors.sdm.noao.edu/tada-test-data/fits-test-data.tgz
    tar xf fits-test-data.tgz
fi
source $tadadir/../tada-tools/dev-scripts/irods_init.sh
echo "#"

function insertsrc () {
    srcpath=$1
    SRCFILES="$SRCFILES $srcpath"
    tele='unknown'
    inst='unknown'
    echo "INSERT OR REPLACE INTO audit (srcpath,telescope,instrument) VALUES ('$srcpath','$tele','$inst');" | sqlite3 $AUDITDB
    
    gen-audit-records.sh -t $tele -i $inst -n valley.sdm.noao.edu $f  > /dev/null
}

