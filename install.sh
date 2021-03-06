#!/bin/bash
# This for use under DEVELOPMENT (NATICA system).
# Run this after code modifications.  Installs TADA python stuff from source.
# Run as sudo (typically under vagrant as vagrant user, no venv active).
# Usually has to be run on both Mountain and Valley hosts.
#
# SEE ALSO:
#   /opt/tada/scripts/tada-valley-install.sh
#     (which is used to provision under Puppet)
#   sudo /sandbox/tada/scripts/updateTadaTables.sh
# SIMILARLY: /opt/data-queue/scripts/dataq-valley-install.sh
#
# EXAMPLES:
#  sudo /sandbox/tadanat/install.sh
#  sudo install.sh -c   # clean first
#

SCRIPT=$(readlink -f $0)        # Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT)   # Absolute path this script is in

usage="USAGE: $cmd [options] [repoDirectiory]
OPTIONS:
  -c:: Clean before install. (/var/tada, queue)
  -v <verbosity>:: higher number for more output (default=0)
"

VERBOSE=0
PROGRESS=0
CLEAN="NO"
while getopts "hcv:" opt; do
    case $opt in
	c)
            CLEAN="YES"
            ;;
	    h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done
#echo "OPTIND=$OPTIND"
for (( x=1; x<$OPTIND; x++ )); do shift; done

RAC=0 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi

repodir=${1:-/sandbox}
installprefix=/opt/tada/venv
echo "Installing (natica) FROM repo: $repodir to $installprefix" 

##############################################################################

#!if [ "$CLEAN" = "YES" ]; then
#!    sudo rm -rf /var/tada/*/*
#!    find /var/tada    
#!    dqcli --clear -s
#!fi

source /opt/tada/venv/bin/activate

##################################################
### Force install of python packages from source
###
echo "#######################################################"
echo "WARNING: NOT rebuilding dataq software!!! in install.sh"
echo "#######################################################"
#!echo "Install: dataq.."
#!pushd $repodir/dataq > /dev/null
#!pylint -E dataq/
#!python3 setup.py install --force --prefix $installprefix
#!popd > /dev/null
###

#!echo 
#!echo "WARNING: NOT rebuilding tada software!!! (in install.sh)"
#!echo 
echo "Install: tada.."
pushd $repodir/tadanat > /dev/null
pylint -E tada/
pylintstatus=$?
if [ $pylintstatus -eq 1 ]; then
    echo "pylint FATAL message for TADA"
    exit 1
fi
if [ $pylintstatus -eq 2 ]; then
    echo "pylint ERROR message for TADA"
    exit 2
fi
python3 setup.py install --force --prefix $installprefix
popd > /dev/null
###
##########################################################


sudo rm /var/log/tada/*.err
sudo service dqd restart > /dev/null
if [ -s /var/log/tada/dqd.err ]; then
    cat /var/log/tada/dqd.err
    echo "ERROR: The 'dqd' service is not running"
    exit 1
else
    echo "dqd restarted successfully."
    #!sudo dqcli --clear
    dqcli --clear
fi

sudo service watchpushd restart > /dev/null
if [ -s /var/log/tada/watchpushd.err ]; then
    cat /var/log/tada/watchpushd.err
    echo "ERROR: The 'watchpushd' service is not running"
    exit 1
else
	echo "watchpushd restarted successfully"
fi

sudo chown tada.tada /var/log/tada/dqcli*.log
sudo chmod 777 /var/log/tada/dqcli*.log

echo "Clear logs /var/log/tada/*"
truncate -s 0 /var/log/tada/*




echo "### INSTALLED: `date`"
echo "############################################################"
