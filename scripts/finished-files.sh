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
LOG=/var/log/tada/submit.log
RESULTS=/tmp/$cmd.$$.results
TIMEOUT=30

usage="USAGE: $cmd [options] match [match ...]
OPTIONS:
  -l <inputLog>:: Results file to read for matches (default=$LOG)
  -p <progress>:: Number of progress updates per second (default=0)
  -r <resultsFile>:: Extracted submit results for matching lines (default=$RESULTS)
  -t <seconds>:: Seconds to wait for match to show up in results (default=$TIMEOUT)
  -v <verbosity>:: higher number for more output (default=0)

"


while getopts "hl:p:r:t:v:" opt; do
    #!echo "opt=<$opt>"
    case $opt in
	h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
            ;;
        l)
            LOG=$OPTARG
            ;;
        p)
            PROGRESS=$OPTARG # how often to report progress
            ;;
        r)
            RESULTS=$OPTARG
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


#! echo "PROGRESS=$PROGRESS"
#! echo "VERBOSE=$VERBOSE"
#! echo "Remaining arguments:"
#! for arg do echo '--> '"\`$arg'" ; done



##############################################################################

#! echo "# Produced by: $cmd" > $RESULTS
echo > $RESULTS # clear old content

maxTries=$TIMEOUT
for str; do
    #!echo "Looking in log for: $str"
    tries=0
    echo -n "# "
    while ! fgrep "$str" $LOG >> $RESULTS; do
	tries=$((tries+1))
	#! echo "tries=$tries"
	echo -n "."
	if [ "$tries" -gt "$maxTries" ]; then
	    echo "Aborted after maxTries=$maxTries: $str"
	    exit 1
	fi
	sleep 1
    done
    echo
done

#! echo "Found them all!"
exit 0

