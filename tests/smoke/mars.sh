#!/bin/bash
# PURPOSE:    Make it easy to do some MARS web services from bash
#

#marshost=mars.sdm.noao.edu
marshost=valley.sdm.noao.edu
marsurl="http://$marshost:8000"
copts="--connect-timeout 10 --max-time 600 -s -S"

function mars_rollback () {
    #echo -n "rolling back..."
    if curl $copts "$marsurl/provisional/rollback/" > /dev/null
    then
        echo "# REMOVED all provisional files before starting."
    else
        echo "# COULD NOT remove all provisional files before starting."
	echo "Tried using: curl $copts $marsurl/provisional/rollback/"
    fi
}

function mars_stuff () {
    if curl $copts "$marsurl/provisional/stuff/" > /dev/null
    then
        echo "# STUFFed files matching 'TADA' into provisional files."
    else
        echo "# COULD NOT stuff."    
	echo "Tried using: curl $copts $marsurl/provisional/stuff/"
    fi
}


function mars_add () {
    archfile=$1
    ffile=$2
    if curl $copts "$marsurl/provisional/add/$archfile/?source=$ffile" >/dev/null
    then
	# full path is  pain for testing
        #!echo "Added provisional name (id=$archfile, source=$ffile)"
        echo "# Added provisional name for $archfile"
    else
        echo "# COULD NOT add $archfile to PROVISIONAL list via ws"
    fi
    #echo "Successful ingest of $archfile."
}
