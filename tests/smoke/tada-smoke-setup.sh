#
# Common setup for running TADA smoke tests.
# Clears database of specially named files, loads test files if needed.
#

#! echo "# Common setup for TADA smoke tests"
source mars.sh
source fsub.sh
mars_stuff
mars_rollback

if [ -d "$tdata" ]; then
    echo "# Data directory ($tdata) exists. Using it!"
else
    echo "# Data directory ($tdata) does not exist. Transfering it"
    rm /sandbox/tada/tests/smoke/fits-test-data.tgz
    wget -nc http://mirrors.sdm.noao.edu/tada-test-data/fits-test-data.tgz
    tar xf fits-test-data.tgz
fi
source /sandbox/tada-tools/dev-scripts/irods_init.sh
echo "#"
