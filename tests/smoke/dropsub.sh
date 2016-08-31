#!MANIFEST="$dir/manifest.out"
#!ARCHLOG="/var/log/tada/archived.manifest"
AUDITDB="/var/log/tada/audit.db"
SMOKEDB="$HOME/.tada/smoke.db"
DROPCACHE="$HOME/.tada/dropcache"

# Maximum seconds waited for a dropped file to show at ingest.
# (excluding files that NEVER make it to ingest)
MAX_FOUND_TIME=0 


CREATE_SMOKEDB="CREATE TABLE expected (
   fits text,
   tele text,
   instrum text,
   success integer);
"

if [ ! -e $SMOKEDB ]; then
    sqlite3 $SMOKEDB "$CREATE_SMOKEDB"
fi

function setup_dropbox_tests () {
    mkdir -p $DROPCACHE

    sqlite3 $AUDITDB "delete from audit;"
    
    rm $SMOKEDB
    sqlite3 $SMOKEDB "$CREATE_SMOKEDB"
    chmod a+rw $SMOKEDB
}

function clean_manifest () {
    rm  $MANIFEST > /dev/null
    touch $MANIFEST 
    date > $ARCHLOG
    chgrp tada $ARCHLOG
}

function record_expected () {
    local fits=$1 # full path to source FITS file
    local YYYMMDD=$2 # e.g. "20160101"
    local TELE_INST=$3
    local expected=$4

    local day="${YYYYMMDD:0:4}-${YYYYMMDD:4:2}-${YYYYMMDD:6:2}"
    IFS='-' read  tele inst <<< "$TELE_INST"

    local sql="INSERT INTO expected VALUES ('$fits','$tele', '$inst', '$expected');"
    sqlite3 $SMOKEDB "$sql"
    #!echo "# RECORD_EXPECTED in $SMOKEDB: sql=$sql"
    #gen-audit-records.sh -d $day -t $tele -i $inst -n $marshost $fits>/dev/null
}

# Wait for FITSFILE to appear in AUDITDB.
# If timeout, RETURN=9. Else, if EXPECTED=ACTUAL RETURN=0, else RETURN=1
# MUST match against specific (fits,tele,instrum) record. NOT just fits.
function wait_for_match () { # (fitsfile, tele_inst) => $STATUS
    local FITS=$1 # full path to source FITS file
    local TELE_INST=$2
    IFS='-' read  tele inst <<< "$TELE_INST"
    local TIMEOUT=${MAX_DROP_WAIT_TIME:-15} # seconds
    
    local sql="SELECT count(*) FROM audit \
WHERE success IS NOT NULL \
 AND srcpath='$FITS' AND telescope='$tele' AND instrument='$inst';"
    local maxTries=$TIMEOUT
    local tries=0
    local STATUS=0
    echo "# DBG-SMOKE: sql=$sql"
    echo "# Waiting up to $TIMEOUT secs for $FITSFILE to be submitted: " 
    echo -n "# "
    while [ `sqlite3 $AUDITDB "$sql"` -eq 0 ]; do
        tries=$((tries+1))
        if [ "$tries" -gt "$maxTries" ]; then
            echo "!"
            echo "# Aborted after $maxTries seconds. Not submitted: $FITS"
            STATUS=9
	    echo "# Timeout exceeded. Aborted wait for $FITS."
            return $STATUS
        fi
        echo -n "."
        sleep 1
    done
    echo "!"
    echo "Found file: $FITS"
    echo "# Found file after $tries seconds."
    if [ "$tries" -gt "$MAX_FOUND_TIME" ]; then
        MAX_FOUND_TIME=$tries
    fi
    sql="SELECT success FROM audit \
WHERE srcpath='$FITS' AND telescope='$tele' AND instrument='$inst';"
    local actual=`sqlite3 $AUDITDB "$sql"` 
    echo "# DBG-SMOKE AUDITDB sql: $sql"
    echo "# DBG-SMOKE AUDITDB actual=$actual"
    
    sql="SELECT success FROM expected \
WHERE fits='$FITS' AND tele='$tele' AND instrum='$inst';"
    local expected=`sqlite3 $SMOKEDB "$sql"`
    
    if [ "$actual" != "$expected" ]; then
        echo "# DBG-SMOKE wait_for_match: actual($actual) != expected($expected)"
        STATUS=1
    else
        echo "# DBG-SMOKE wait_for_match: actual=expected"
    fi
    return $STATUS
}

# drop one file to mountain dropbox (ingest may Pass or Fail)
#   copy to pre-drop, add personality, record expected, drop to TADA
function dropfile () {

    local FITSFILE=$1
    local DATE=$2 # e.g. "20160101"
    local TELE_INST=$3
    local expected=$4 # {1=PASS, 0=FAIL}
    local BNAME=`basename $FITSFILE`
    local boxhost="mountain.`hostname --domain`"

    mkdir -p $DROPCACHE
    dropfile=$DROPCACHE/$DATE/${TELE_INST}/$BNAME
    mkdir -p `dirname $dropfile`
    cp $FITSFILE $dropfile
    #!chmod -R a+rwX $DROPCACHE

    record_expected $FITSFILE $DATE ${TELE_INST} $expected

    echo "# DBG-SMOKE: add YAML in $dropfile ($FITSFILE)"
    add_test_personality.sh $FITSFILE $dropfile
    rsync -az --password-file ~/.tada/rsync.pwd \
      $DROPCACHE/ tada@$boxhost::dropbox

    # wait for file to make it through, and capture ingest status
    wait_for_match $FITSFILE ${TELE_INST}
    return $?
}

function passdrop () {
    dropfile $1 $2 $3 1
}

function faildrop () {
    dropfile $1 $2 $3 0
}


function insertsrc () {
    local srcpath=$1
    local SRCFILES="$SRCFILES $srcpath"
    local tele='unknown'
    local inst='unknown'
    echo "INSERT OR REPLACE INTO audit (srcpath,telescope,instrument) VALUES ('$srcpath','$tele','$inst');" | sqlite3 $AUDITDB
    
    gen-audit-records.sh -t $tele -i $inst -n $marshost $f  > /dev/null
}

# Get drop status from Mountain    
function sbox () {
    local mtnhost="mountain.`hostname --domain`"
    local statusdir="$SCRIPTDIR/remote_status"
    mkdir -p $statusdir
    rsync -a --password-file ~/.tada/rsync.pwd tada@$mtnhost::statusbox $statusdir
    find $mydir -type f
}

# drop directory to Mountain Drop BOX
function mdbox () {
    clean_manifest
    local srcdir=$1
    local MAXRUNTIME=120  # max seconds to wait for all files to be submitted
    local boxhost="mountain.`hostname --domain`"
    for f in `find $srcdir \( -name "*.fits" -o -name "*.fits.fz" \)`; do
        # Force all fits files to be touched on remote (which creates event)
        add_test_personality.sh $f
        touch $f
        #! echo "$f" >> $MANIFEST
    insertsrc $f
    done
    echo "# List of files submitted is in: $AUDITDB"
    #rsync -aiz --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    rsync -az  --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    # INFO     SUCCESSFUL submit; /var/tada/cache/20141224/kp09m-hdi/c7015t0267b00.fits.fz as /noao-tuc-z1/mtn/20141223/kp09m/2014B-0711/k09h_141224_115224_zri_TADASMOKE,.fits.fz,
    echo -n "# Waiting up to $MAXRUNTIME secs for all files to be submitted..." 
    #!finished-db.sh -v 1 -t $MAXRUNTIME $SRCFILES
    finished-db.sh        -t $MAXRUNTIME $SRCFILES
}

# drop directory to Valley Drop BOX
function vdbox () {
    clean_manifest
    local srcdir=$1
    local MAXRUNTIME=90  # max seconds to wait for all files to be submitted
    local boxhost="valley.`hostname --domain`"
    for f in `find $srcdir \( -name "*.fits" -o -name "*.fits.fz" \)`; do
        # Force all fits files to be touched on remote (which creates event)
        add_test_personality.sh $f
        touch $f
        #!echo "$f" >> $MANIFEST
    insertsrc $f
    done
    echo "# List of files submitted is in: $MANIFEST"
    rsync -az --password-file ~/.tada/rsync.pwd $srcdir tada@$boxhost::dropbox
    echo -n "# Waiting up to $MAXRUNTIME secs for all files to be submitted..." 
    #!finished-log.sh -t $MAXRUNTIME -l $ARCHLOG $MANIFEST
    finished-db.sh -t $MAXRUNTIME $SRCFILES
}

