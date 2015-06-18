#!/bin/bash -e
# PURPOSE: Waits until all strings in a list show up in a file.
#   (or TIMEOUT exceeded)
#
# EXAMPLE:
#
# AUTHORS: S.Pothier

cmd=`basename $0`
dir=`dirname $0`

#Absolute path to this script
SCRIPT=$(readlink -f $0)
#Absolute path this script is in
SCRIPTPATH=$(dirname $SCRIPT)

VERBOSE=0
PROGRESS=0
MANIFEST=/var/log/tada/submit.manifest
TIMEOUT=30

usage="USAGE: $cmd [options] match [match ...]
OPTIONS:
  -m <manifest>:: File to read for matches (default=$MANIFEST)
  -p <progress>:: Number of progress updates per second (default=0)
  -t <seconds>:: Seconds to wait for match to show up in manifest (default=$TIMEOUT)
  -v <verbosity>:: higher number for more output (default=0)

"


while getopts "hm:p:t:v:" opt; do
    #!echo "opt=<$opt>"
    case $opt in
	h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
            ;;
        m)
            MANIFEST=$OPTARG
            ;;
        p)
            PROGRESS=$OPTARG # how often to report progress
            ;;
        t)
            TIMEOUT=$OPTARG
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
#! echo "OPTIND=$OPTIND"
for (( x=1; x<$OPTIND; x++ )); do shift; done


RAC=1 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi


##############################################################################



maxTries=$TIMEOUT
for str; do
    if [ "$VERBOSE" -gt 0 ]; then
       echo "Looking in manifest for: $str"
       echo "# Waiting $maxTries seconds for $str in '$MANIFEST'"
    fi
    tries=0
    echo -n "# wait"
    while ! grep -l -F "$str" $MANIFEST > /dev/null; do
	tries=$((tries+1))
	echo -n "."
	if [ "$tries" -gt "$maxTries" ]; then
	    echo
	    echo "Aborted after maxTries=$maxTries: $str"
	    exit 1
	fi
	sleep 1
    done
    echo " Done in $tries seconds"
done

exit 0

