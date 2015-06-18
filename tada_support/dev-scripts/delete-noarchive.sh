#!/bin/bash -e
# PURPOSE: Delete noarchive
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

datadir=/var/tada/noarchive

echo "Are you SURE you want to delete the NOARCHIVE directory tree?"

read ans

if [ "$ans" == "yes" ]; then
    rm -rf $datadir/*
    echo "Done"
else
    echo "You did not answer 'yes'.  Nothing deleted!"
    exit 1
fi
