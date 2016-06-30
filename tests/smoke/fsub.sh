#!/bin/bash

export PATH=/sandbox/tada-cli/scripts:$PATH

###########################################
### fits_submit
###
function fsub () {
    ffile=$1; shift
    add_test_personality.sh $ffile
    #pers=""
    pers="-p ${ffile}.yaml"
    if [ ! -r ${ffile}.yaml ]; then
	    md5=`md5sum ${ffile}  | cut -d ' ' -f 1`
	    cat > ${ffile}.yaml <<EOF
params:
  filename: ${ffile}
  md5sum: $md5
EOF
    fi
    ppath="/var/tada/personalities"
    for p; do
	    pers="$pers -p $ppath/$p/$p.yaml"
    done
    #~msg=`fits_submit -p smoke $pers $ffile 2>&1 `
    msg=`direct_submit --loglevel DEBUG -p $ppath/ops/smoke.yaml $pers $ffile 2>&1 `
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
        echo "EXECUTED: direct_submit -p $ppath/ops/smoke.yaml $pers $tailffile"  
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
    msg=`fits_compliant --header $ffile  2>&1`
    status=$?
    msg=`echo $msg | perl -pe "s|$tdata||g"`
    echo "$msg"
    return $status
}


