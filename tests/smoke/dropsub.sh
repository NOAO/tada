function clean_manifest () {
    rm  $MANIFEST > /dev/null
    touch $MANIFEST
    date > $ARCHLOG
    chgrp tada $ARCHLOG
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

# PREPARE to drop one file to mountain dropbox
# use "dropcache" to submit a set of files 
function dropfile () {
    INSTRUMENT=$1
    FITSFILE=$2
    DATE="20160101"
    CACHE="$HOME/.tada/dropcache"
    BNAME=`basename $FITSFILE`

    mkdir -p $CACHE
    cp $FITSFILE $CACHE/$DATE/$INSTRUMENT/$BNAME
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

