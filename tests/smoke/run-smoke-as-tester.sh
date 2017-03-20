#!/bin/bash
# PURPOSE: Run TADA smoke test.
#
# EXAMPLE:
#   # For Dev (vagrant) test
#   cd ~/sandbox/vagrant-tada;~/sandbox/tada/tests/smoke/run-smoke-as-tester.sh
#
#   # For PAT test
#   ~/sandbox/tada/tests/smoke/run-smoke-as-tester.sh val.pat.sdm.noao.edu
#
# AUTHORS: S.Pothier

cmd=`basename $0`
dir=`dirname $0`

SCRIPT=$(readlink -f $0)      #Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT) #Absolute path this script is in

usage="USAGE: $cmd [options] [hostname]
OPTIONS:
  -v <verbosity>:: higher number for more output (default=0)

hostname:: Name of valley host to run test on (default vagrant valley)

EXAMPLES:
   # For Dev (vagrant) test 
   cd ~/sandbox/vagrant-tada; ~/sandbox/tada/tests/smoke/run-smoke-as-tester.sh

   # For PAT test
   ~/sandbox/tada/tests/smoke/run-smoke-as-tester.sh val.pat.sdm.noao.edu
"

VERBOSE=0
while getopts "hv:" opt; do
    echo "opt=<$opt>"
    case $opt in
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



HOSTNAME=${1:-vagrant}


##############################################################################


#service dqd restart
#service watchpushd restart

#su - tester
#source /opt/tada/venv/bin/activate
#/opt/tada/tests/smoke/smoke.all.sh

echo "Running TADA smoke test on: \"$HOSTNAME\" " `date`

venv="source /opt/tada/venv/bin/activate"
if [ "$HOSTNAME" = "vagrant" ]; then
    port=`vagrant --machine-readable port valley \
| grep forwarded_port | cut -d, -f5`
    ssh -p $port tester@localhost "$venv; /sandbox/tada/tests/smoke/smoke.all.sh"
else
    ssh  tester@$HOSTNAME "$venv; /opt/tada/tests/smoke/smoke.all.sh"
fi

# Add the following lines right below the pam_rootok.so line in your
# /etc/pam.d/su:
#
# auth       [success=ignore default=1] pam_succeed_if.so user = tester
# auth       sufficient   pam_succeed_if.so use_uid user = vagrant
