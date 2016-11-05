#!/bin/bash
# PURPOSE:    Make it easy to do some MARS web services from bash
#

#marshost=mars.sdm.noao.edu
#marshost=valley.sdm.noao.edu
#marshost=`grep mars_host /etc/tada/hiera.yaml | cut -f2 -d' '`
marshost="$MARSHOST"
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


# Add filename to provisional list in MARS.
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

# Insert an initial audit record (usually done from a dome)
function dome_audit () {
    local md5=$1   # md5sum of original (dome) FITS file
    local FITS=$2  # full path of orignal (dome) FITS file
    local DATE=$3  # YYYYMMDD, obsday
    local TELE_INST=$4
    local MARS_HOST=${5:-$marshost}
    
    JSONFILE="/tmp/dropsub.$md5.json"
    IFS='-' read  tele inst <<< "$TELE_INST"
    DAY="${DATE:0:4}-${DATE:4:2}-${DATE:6:2}"
    cat > $JSONFILE <<EOF
{ "observations": [
  { "md5sum": "$md5", 
    "srcpath": "$FITS", 
    "obsday": "$DAY", 
    "telescope": "$tele", 
    "instrument": "$inst" 
  } ] }
EOF
    curl -H "Content-Type: application/json" \
         -d @$JSONFILE \
         http://$MARS_HOST:8000/audit/source/ > /dev/null 2>&1
    
}
