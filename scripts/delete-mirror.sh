#!/bin/bash -e
# PURPOSE: Delete mountain-mirror 
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

MIRROR=/var/tada/mountain-mirror

echo "Are you SURE you want to delete the mountain mirror?"

read ans

if [ "$ans" == "yes" ]; then
    rm -rf $MIRROR/*
    echo "Done"
else
    echo "You did not answer 'yes'.  Nothing deleted!"
    exit 1
fi
