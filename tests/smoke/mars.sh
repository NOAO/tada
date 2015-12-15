#!/bin/bash
# PURPOSE:    Make it easy to do some MARS web services from bash
#

marsurl="http://mars.sdm.noao.edu:8000"
copts="--connect-timeout 10 --max-time 600 -s -S"

function mars_rollback () {
    if curl $copts "$marsurl/provisional/rollback/" > /dev/null
    then
        echo "REMOVED all provisional files before starting."
    else
        echo "COULD NOT remove all provisional files before starting."    
    fi
}

function mars_stuff () {
    if curl $copts "$marsurl/provisional/stuff/" > /dev/null
    then
        echo "STUFFed files matching 'TADA' into provisional files."
    else
        echo "COULD NOT stuff."    
    fi
}


function mars_add () {
    archfile=$1
    ffile=$2
    if curl $copts "$marsurl/provisional/add/$archfile/?source=$ffile" >/dev/null
    then
        echo "Added provisional name (id=$archfile, source=$ffile)"
    else
        echo "COULD NOT add $archfile to PROVISIONAL list via ws"
    fi
    echo "Successful ingest of $archfile."
}
