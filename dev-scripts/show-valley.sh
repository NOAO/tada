#!/bin/bash -e
# PURPOSE: Show TADA related state of Valley ("Base") machine
#
# EXAMPLE:
#
# AUTHORS: S.Pothier

cmd=`basename $0`
#Absolute path to this script
SCRIPT=$(readlink -f $0)
#Absolute path this script is in
SCRIPTPATH=$(dirname $SCRIPT)

usage="USAGE: $cmd [options] [reportFile]
OPTIONS:
  -v <verbosity>:: higher number for more output (default=0)
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
RAC=0 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi

if [ "$USER" != "tada" ]; then
    echo "Must run this script as 'tada' user. Aborting" 1>&2
    exit 1
fi

##############################################################################

icmdpath='/usr/local/share/applications/irods3.3.1/iRODS/clients/icommands/bin'
MIRROR=/var/tada/mountain-mirror
NOARCHIVE=/var/tada/noarchive

irodsroot=/noao-tuc-z1/tada/
rdir=~/report
mkdir -p $rdir

echo -e "\n#############################################################"
echo -e "### SHOW Valley machine"

echo -e "\n# List of files put in Archive iRODS"
$icmdpath/irsync -l -r -s i:${irodsroot} ~/fakeZone | awk '{print $1}' > $rdir/arc.list
cat $rdir/arc.list

echo -e "\n# Content of storage"
find /var/tada -type f

echo -e "\n# Content of SUBMIT Queue"
dqcli --list active
dqcli --list inactive


echo -e "\nSummary:"
fcnt=`grep -c fits $rdir/arc.list`
hcnt=`grep -c hdr $rdir/arc.list`
mcnt=`find $MIRROR -type f | wc -l`
ncnt=`find $NOARCHIVE  -type f | wc -l`
icnt=`dqcli --list inactive | wc -l`; n=$((icnt--))
acnt=`dqcli --list active | wc -l`; n=$((acnt--))
echo -e "  FITS files in archive: $fcnt\tHDR  files in archive: $hcnt"
echo -e "  Non-fits files stored: $ncnt"
echo -e "  Inactive queue: $icnt      \tNot archived fits files: $mcnt"
echo -e "  Active queue:   $acnt"

echo -e ""
echo -e "### DONE: show Valley machine"
echo -e "#############################################################\n"




##############################################################################
# Local Variables:
# fill-column:75
# mode:sh
# End:

