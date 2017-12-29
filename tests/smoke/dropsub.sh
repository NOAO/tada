# Functions (subroutines) for dropbox related tests

#!MANIFEST="$dir/manifest.out"
#!ARCHLOG="/var/log/tada/archived.manifest"
AUDITDB="/var/log/tada/audit.db"
SMOKEDB="$HOME/.tada/smoke.db"
DROPCACHE="$HOME/.tada/dropcache"

# sqlite3 --header $SMOKEDB "select success,fits,updated from expected"
# sqlite3 --header $AUDITDB "select success,srcpath,recorded from audit"


# Maximum seconds waited for a dropped file to show at ingest.
# (excluding files that NEVER make it to ingest)
MAX_FOUND_TIME=0 


CREATE_SMOKEDB="CREATE TABLE expected (
   fits text,
   tele text,
   instrum text,
   success integer,
   updated datetime
);
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
    rm -rf ~tester/.tada/mountain-logs
    rm -rf ~tester/.tada/dropcache
    echo "COMPLETED setup for dropbox tests. "
    echo "   Removed ~tester/.tada/mountain-logs/"
    echo "   Removed ~tester/.tada/dropcache/"
}

# Estimate time to upload FITS (iput) at rate=10mbps
function up_secs () {
    local FITS=$1
    local bytes=`du -b $FITS | cut -f1`
    echo "2 k $bytes 8 * 1000000 / 10 / p" | dc
}

function audit_vs_expected () {
    local audit=NA
    local exptd=NA
    for f in `sqlite3 $SMOKEDB "SELECT fits FROM expected"`; do
        audit=`sqlite3 $AUDITDB "SELECT success FROM audit WHERE srcpath='$f'"`
        exptd=`sqlite3 $SMOKEDB "SELECT success FROM expected WHERE fits='$f'"`
        if [ "$audit" = "$exptd" ]; then
            echo "PASS: $f; expected=$exptd  audit=$audit"
        elif [ -z "$audit" ]; then
            echo "FAIL: $f; not in audit"            
        else
            echo "FAIL: $f; expected=$exptd  audit=$audit" 
        fi
    done
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
    local now=`date --rfc-3339=seconds`
    local day="${YYYYMMDD:0:4}-${YYYYMMDD:4:2}-${YYYYMMDD:6:2}"
    IFS='-' read  tele inst <<< "$TELE_INST"

    local sql="INSERT INTO expected VALUES ('$fits','$tele', '$inst', '$expected', '$now');"
    sqlite3 $SMOKEDB "$sql"
    #!echo "# RECORD_EXPECTED in $SMOKEDB: sql=$sql"
    #gen-audit-records.sh -d $day -t $tele -i $inst -n $marshost $fits>/dev/null
}

# Wait for FITSFILE to appear in MARS AUDIT service.
# curl "http://localhost:8000/audit/query/20161229/soar/goodman/0084.leia.fits/"    
function wait_for_audit_match() {
    local TIMEOUT=$1 # seconds
    local FITS=$2 # full path to source FITS file
    local TELE_INST=$3
    IFS='-' read  tele inst <<< "$TELE_INST"
    base=`basename $FITS`
    q="$DAY/$tele/$inst/$base/"
    }
    
# Wait for FITSFILE to appear in AUDITDB.
# If timeout, RETURN=9. Else, if EXPECTED=ACTUAL RETURN=0, else RETURN=1
# MUST match against specific (fits,tele,instrum) record. NOT just fits.
function wait_for_match () { # (fitsfile, tele_inst) => $STATUS
    local TIMEOUT=$1 # seconds
    local FITS=$2 # full path to source FITS file
    local TELE_INST=$3
    IFS='-' read  tele inst <<< "$TELE_INST"
    local auditsql="SELECT success FROM audit WHERE srcpath='$FITS';"
    # AND srcpath='$FITS' AND telescope='$tele' AND instrument='$inst';"
    expectedsql="SELECT success FROM expected WHERE fits='$FITS';"
    # AND tele='$tele' AND instrum='$inst';"
    local sql="SELECT count(*) FROM audit WHERE success IS NOT NULL AND srcpath='$FITS';"
    local maxTries=$TIMEOUT
    local tries=0
    local STATUS=0
    echo "# Waiting up to $TIMEOUT secs for $FITSFILE to be submitted: " 
    echo -n "# "
    while [ `sqlite3 $AUDITDB "$sql"` -eq 0 ]; do
        tries=$((tries+1))
        if [ "$tries" -gt "$maxTries" ]; then
            echo "!"
            echo "# Aborted after $maxTries seconds. Not submitted: $FITS"
            STATUS=9
            return $STATUS
        fi
        echo -n "."
        sleep 1
    done
    echo "!"
    echo "Found file: $FITS"
    echo "# Found file after $tries seconds in AUDITDB ($AUDITDB)."
    if [ "$tries" -gt "$MAX_FOUND_TIME" ]; then
        MAX_FOUND_TIME=$tries
    fi
    local actual=`sqlite3 $AUDITDB "$auditsql"` 
    local expected=`sqlite3 $SMOKEDB "$expectedsql"`
    if [ "$actual" != "$expected" ]; then
        #echo "# DBG-SMOKE wait_for_match: actual($actual) != expected($expected)"
        STATUS=1
    else
        x=1
        #echo "# DBG-SMOKE wait_for_match: actual=expected"
    fi
    return $STATUS
}

# drop a whole directory to dropbox on given (default=valley) host 
function dropdir () {
    local SRCDIR=$1
    #local BOXHOST=${2:-`grep valley_host /etc/tada/hiera.yaml | cut -d' ' -f2`}
    local BOXHOST=${2:-$VALHOST}
    # use create-audit-for-drop.sh to create JSON file if needed
    local JSONFILE="$SRCDIR/dome-audit.json"
    #local MARSHOST=`grep mars_host /etc/tada/hiera.yaml | cut -d' ' -f2`

    echo "Posting JSONFILE ($JSONFILE) to MARS ($MARSHOST)"
    curl -H "Content-Type: application/json" \
         -d @$JSONFILE http://$MARSHOST:8000/audit/source/ \
         > /dev/null 2>&1
    echo "Sending SRCDIR ($SRCDIR) to dropbox on $BOXHOST"
    find $SRCDIR/  -type f -name "*.fits" -o -name "*.fz" -exec touch {} \;
    rsync -az --password-file ~/.tada/rsync.pwd $SRCDIR/ tada@$BOXHOST::dropbox
    echo "RSYNC to dropbox completed. Now check RESULTS of dropbox."
}

# drop one file to mountain dropbox (ingest may Pass or Fail)
#   copy to pre-drop, add personality, record expected, drop to TADA
function dropfile () {
    if [ $# -lt 5 ]; then
        echo "ERROR: dropfile needs 5 arguments"
        return 9
    fi
    local TIMEOUT=$1 # seconds to wait for file to ingest (includes transfer)
    local FITSFILE=$2
    local DATE=$3 # e.g. "20160101"
    local TELE_INST=$4
    local expected=$5 # {1=PASS, 0=FAIL}
    local BNAME=`basename $FITSFILE`
    #local boxhost=${DROPHOST:-"mountain.`hostname --domain`"}
    local boxhost=${DROPHOST:-"$MTNHOST"}

    echo "# Using dropbox on: $boxhost"

    dropfile=$DROPCACHE/$DATE/${TELE_INST}/$BNAME
    mkdir -p `dirname $dropfile`
    echo "# DBG: dropping \"$FITSFILE\" to \"$dropfile\""
    cp $FITSFILE $dropfile
    #!chmod -R a+rwX $DROPCACHE

    record_expected $FITSFILE $DATE ${TELE_INST} $expected
    
    #echo "# DBG-SMOKE: add YAML in $dropfile ($FITSFILE)"
    add_test_personality.sh $FITSFILE $dropfile
    md5=`grep md5sum $dropfile.yaml | cut -b 13-`
    JSONFILE="$DROPCACHE/dropsub.$md5.json"
    IFS='-' read  tele inst <<< "$TELE_INST"
    DAY="${DATE:0:4}-${DATE:4:2}-${DATE:6:2}"
    cat > $JSONFILE <<EOF
{ "observations": [
  { "md5sum": "$md5", 
    "srcpath": "$FITSFILE", 
    "obsday": "$DAY", 
    "telescope": "$tele", 
    "instrument": "$inst" 
  } ] }
EOF
    curl -H "Content-Type: application/json" \
         -d @$JSONFILE \
         http://$marshost:8000/audit/source/ > /dev/null 2>&1
    rsync -az --password-file ~/.tada/rsync.pwd $DROPCACHE/ tada@$boxhost::dropbox
    #!cmd="rsync -az --password-file ~/.tada/rsync.pwd $DROPCACHE/ tada@$boxhost::dropbox"
    #!echo "DBG-EXECUTE: $cmd"
    #!eval $cmd

    # wait for file to make it through, and capture ingest status
    wait_for_match $TIMEOUT $FITSFILE ${TELE_INST}
    return $?
}

function passdrop () {
    dropfile $1 $2 $3 $4 1
}

function faildrop () {
    dropfile $1 $2 $3 $4 0
}


function pylogfilter () {
    local logfile=$1
    local marker=$2
    local filename=$3

    csplit --prefix=$sto/xx --quiet $logfile "%$marker%"+1
    grep `basename $filename .fz` $sto/xx00 \
        | grep  "WARNING \| ERROR " | cut -d' ' -f3- 
}

# All INFO, WARNING and ERROR lines for this smoke-test run
function pylogrun () {
    local logfile=$1
    local marker=$2

    csplit --prefix=$sto/xx --quiet $logfile "%$marker%"+1
    sort $sto/xx00 > $sto/sorted-xx00
    grep  "INFO \| WARNING \| ERROR " $sto/sorted-xx00 | cut -d' ' -f3- 
}

function mtnlogrun () {
    local log=$1
    local start=$2

    tail -n +$((start+1)) $log | sort \
        | grep  "INFO \| WARNING \| ERROR " | cut -d' ' -f3- 
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
    local mtnhost="$MTNHOST"
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
    local boxhost="$MTNHOST"
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

