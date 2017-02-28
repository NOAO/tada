#!/bin/bash

export PATH=/sandbox/tada-cli/scripts:/opt/tada-cli/scripts:$PATH

function zero_archive_timeout () {
    sed -i.bak 's/arch_timeout:.*/arch_timeout: 0/' /etc/tada/hiera.yaml
    chmod a+r /etc/tada/hiera.yaml
    echo "Changed Ingest Service timeout to ZERO"
}

function restore_archive_timeout () {
    cp /etc/tada/hiera.yaml.bak /etc/tada/hiera.yaml
    echo "Restored Ingest Service timeout to previous value"
    }

###########################################
### fits_submit
###
function fsub () {
    ffile=$1; shift
    add_test_personality.sh $ffile $ffile
    #!md5=`grep md5sum $ffile.yaml | cut -b 13-`
    #!dome_audit $md5 $ffile "$DATE" "$TELE_INST" "$MARS_HOST"

    #pers=""
    pers="-p ${ffile}.yaml"
#!    if [ ! -r ${ffile}.yaml ]; then
#!	    md5=`md5sum ${ffile}  | cut -d ' ' -f 1`
#!	    cat > ${ffile}.yaml <<EOF
#!params:
#!  filename: ${ffile}
#!  md5sum: $md5
#!EOF
#!    fi
    ppath="/var/tada/personalities"
    for p; do
	    pers="$pers -p $ppath/$p/$p.yaml"
    done
    #~msg=`fits_submit -p smoke $pers $ffile 2>&1 `
    msg=`/opt/tada/venv/bin/direct_submit --loglevel DEBUG -p $ppath/ops/smoke.yaml $pers $ffile 2>&1 `
    status=$?
    msg=`echo $msg | perl -pe "s|$tdata||"`
    #echo "msg=$msg"
    if [ $status -eq 0 ]; then
        # e.g. msg="SUCCESS: archived /sandbox/tada/tests/smoke/data/obj_355.fits as /noao-tuc-z1/mtn/20141219/WIYN/2012B-0500/uuuu_141220_130138_uuu_TADATEST_2417885023.fits"
        irodsfile=`echo $msg | cut -s --delimiter=' ' --fields=5`
        archfile=`basename $irodsfile`
        echo $msg 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
        mars_add "$archfile" "$ffile"
        echo ""
    else
	tailffile=`echo $ffile | perl -pe "s|$tdata|/DATA|"`
        echo "EXECUTED: /opt/tada/venv/bin/direct_submit -p $ppath/ops/smoke.yaml $pers $tailffile"  
        echo $msg
    fi
    return $status
}

#############################################
### hlsp_submit (High Level Science Products)
###
function hsub () {
    target=$1; shift
    ffile=$1; shift
    add_test_personality.sh $ffile $ffile
    #!md5=`grep md5sum $ffile.yaml | cut -b 13-`
    #!dome_audit $md5 $ffile "$DATE" "$TELE_INST" "$MARS_HOST"

    #pers=""
    pers="-p ${ffile}.yaml"
    ppath="/var/tada/personalities"
    for p; do
	    pers="$pers -p $ppath/$p/$p.yaml"
    done
    cmd="/opt/tada/venv/bin/direct_submit --target ${target} --loglevel DEBUG -p $ppath/ops/smoke.yaml $pers $ffile "
    #echo "cmd=$cmd"
    msg=`$cmd  2>&1`
    status=$?
    #echo "msg=$msg"
    #echo "status=$status"

    msg=`echo $msg | perl -pe "s|$tdata||"`
    if [ $status -eq 0 ]; then
        irodsfile=`echo $msg | cut -s --delimiter=' ' --fields=5`
        archfile=`basename $irodsfile`
        echo $msg 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
        mars_add "$archfile" "$ffile"
        echo ""
    else
	tailffile=`echo $ffile | perl -pe "s|$tdata|/DATA|"`
        echo "EXECUTED: /opt/tada/venv/bin/direct_submit --target ${target} -p $ppath/ops/smoke.yaml $pers $tailffile"  
        echo $msg
    fi
    return $status
}


###########################################
### pipeline_submit
###
function psubmit () {
    ffile=$1; shift
    #msg=`pipeline_submit $ffile 2>&1`
    #!status=$?
    pipeline_submit $ffile 2>&1 | perl -pe 's|as /noao-tuc-z1/.*||'
}


###########################################
### fits_compliant
###
function fcom () {
    ffile=$1
    msg=`/opt/tada/venv/bin/fits_compliant --header $ffile  2>&1`
    status=$?
    msg=`echo $msg | perl -pe "s|$tdata||g"`
    echo "$msg"
    return $status
}


