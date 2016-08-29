#!MANIFEST="$dir/manifest.out"
#!ARCHLOG="/var/log/tada/archived.manifest"
AUDITDB="/var/log/tada/audit.db"
SMOKEDB="$HOME/.tada/smoke.db"
DROPCACHE="$HOME/.tada/dropcache"


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
}

function clean_manifest () {
    rm  $MANIFEST > /dev/null
    touch $MANIFEST 
    date > $ARCHLOG
    chgrp tada $ARCHLOG
}

function record_expected () {
    fits=$1 # full path to source FITS file
    YYYMMDD=$2 # e.g. "20160101"
    TELE_INST=$3
    expected=$4

    day="${YYYYMMDD:0:4}-${YYYYMMDD:4:2}-${YYYYMMDD:6:2}"
    IFS='-' read  tele inst <<< "$TELE_INST"

    sql="INSERT INTO expected VALUES ('$fits','$tele', '$inst', '$expected');"
    sqlite3 $SMOKEDB "$sql"
    #!echo "RECORD_EXPECTED in $SMOKEDB: sql=$sql"

    #gen-audit-records.sh -d $day -t $tele -i $inst -n $marshost $fits>/dev/null
}

# Wait for FITSFILE to appear in AUDITDB.
# If timeout, RETURN=9. Else, if EXPECTED=ACTUAL RETURN=0, else RETURN=1
# MUST match against specific (fits,tele,instrum) record. NOT just fits.
function wait-n-match () { # (fitsfile, tele_inst) => $STATUS
    FITS=$1 # full path to source FITS file
    TELE_INST=$2
    IFS='-' read  tele inst <<< "$TELE_INST"
    TIMEOUT=15 # seconds

    sql="SELECT count(*) FROM audit \
WHERE success IS NOT NULL \
 AND srcpath='$FITS' AND telescope='$tele' AND instrument='$inst';"
    maxTries=$TIMEOUT
    tries=0
    STATUS=0
    #!echo "DBG-SMOKE: sql=$sql"
    echo "# Waiting up to $TIMEOUT secs for $FITSFILE to be submitted: " 
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
    echo "Found file after $tries seconds."
    
    sql="SELECT success FROM audit \
WHERE srcpath='$FITS' AND telescope='$tele' AND instrument='$inst';"
    actual=`sqlite3 $AUDITDB "$sql"` 

    sql="SELECT success FROM expected \
WHERE fits='$FITS' AND tele='$tele' AND instrum='$inst';"
    expected=`sqlite3 $SMOKEDB "$sql"`

    if [ "$actual" != "$expected" ]; then
	echo "DBG-SMOKE wait-n-match: actual($actual)!=expected($expected)"
	STATUS=1
    else
	echo "DBG-SMOKE wait-n-match: actual=expected"
    fi
    return $STATUS
}

# drop one file to mountain dropbox, ingest may Pass or Fail
function dropfile () {
    FITSFILE=$1
    DATE=$2 # e.g. "20160101"
    TELE_INST=$3
    expected=$4 # {1=PASS, 0=FAIL}
    BNAME=`basename $FITSFILE`
    boxhost="mountain.`hostname --domain`"

    # Drop file to tada:
    #   copy to pre-drop, add personality, record expected, drop to TADA

    mkdir -p $DROPCACHE
    dropfile=$DROPCACHE/$DATE/${TELE_INST}/$BNAME
    mkdir -p `dirname $dropfile`
    cp $FITSFILE $dropfile
    #!chmod -R a+rwX $DROPCACHE
    
    #!echo "DBG-SMOKE: cp $FITSFILE -> $dropfile"

    record_expected $FITSFILE $DATE ${TELE_INST} $expected

    #!echo "DBG-SMOKE: add YAML in $dropfile ($FITSFILE)"
    add_test_personality.sh $FITSFILE $dropfile
    rsync -az --password-file ~/.tada/rsync.pwd \
	  $DROPCACHE/ tada@$boxhost::dropbox

    # wait for file to make it through, and capture ingest status
    wait-n-match $FITSFILE ${TELE_INST}
    echo $STATUS
}

function passdrop () {
    dropfile $1 $2 $3 1
}
function faildrop () {
    dropfile $1 $2 $3 0
}


function insertsrc () {
    srcpath=$1
    SRCFILES="$SRCFILES $srcpath"
    tele='unknown'
    inst='unknown'
    echo "INSERT OR REPLACE INTO audit (srcpath,telescope,instrument) VALUES ('$srcpath','$tele','$inst');" | sqlite3 $AUDITDB
    
    gen-audit-records.sh -t $tele -i $inst -n $marshost $f  > /dev/null
}

# Get drop status from Mountain    
function sbox () {
    mtnhost="mountain.`hostname --domain`"
    statusdir="$SCRIPTDIR/remote_status"
    mkdir -p $statusdir
    rsync -a --password-file ~/.tada/rsync.pwd tada@$mtnhost::statusbox $statusdir
    find $mydir -type f
}

# drop directory to Mountain Drop BOX
function mdbox () {
    clean_manifest
    srcdir=$1
    MAXRUNTIME=120  # max seconds to wait for all files to be submitted
    boxhost="mountain.`hostname --domain`"
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
    srcdir=$1
    MAXRUNTIME=90  # max seconds to wait for all files to be submitted
    boxhost="valley.`hostname --domain`"
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

