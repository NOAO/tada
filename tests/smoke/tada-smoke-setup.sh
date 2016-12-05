#
# Common setup for running TADA smoke tests.
# Clears database of specially named files, loads test files if needed.
#

#! echo "# Common setup for TADA smoke tests"
source /etc/tada/smoke-config.sh
source fsub.sh
source mars.sh
mars_stuff
mars_rollback

if [ -d "$tdata" ]; then
    echo "# Data directory ($tdata) exists. Using it!"
else
    echo "# DISABLED:Data directory ($tdata) does not exist. Transfering it"
    #rm $SCRIPTDIR/fits-test-data.tgz
    #wget -nc http://mirrors.sdm.noao.edu/tada-test-data/fits-test-data.tgz
    #tar xf fits-test-data.tgz
fi
#!!source $tadadir/../tada-tools/dev-scripts/irods_init.sh
#!ICMDS="/usr/local/share/applications/irods3.3.1/iRODS/clients/icommands/bin"
#!ln -s  ~/.irods/irodsEnv.dev ~/.irods/.irodsEnv
#!$ICMDS/iinit < /etc/tada/iinit.in

#!if [ ! -d ~/.irods ]; then
#!    #source $tadadir/../tada-tools/dev-scripts/irods_init.sh
#!    echo "ERROR: Smoke tests can only be run from valley with valid irods setup in ~/.irods"
#!    exit 1
#!fi


echo "# TADA packages installed:"
yum list installed | grep tada
yum list installed | grep dataq
echo "# Hosts used:"
#grep _host /etc/tada/*.conf /etc/tada/hiera.yaml | grep -v \#
echo "  DQHOST=$DQHOST"
echo "  ARCHHOST=$ARCHHOST"
echo "  IRODSHOST=$IRODSHOST"
echo "  MARSHOST=$MARSHOST"
echo "  MTNHOST=$MTNHOST"
echo "  VALHOST=$VALHOST"

#echo "tada version: " `fits_compliant --version`

echo "#"



