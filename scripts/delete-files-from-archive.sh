#!/bin/bash
filelist=$1
nsabin=/home/arcsoft/nsabin
for filename in `cat $filelist`; do
    base=`basename $filename`
    echo "Deleting file: $base"
    $nsabin/remove_fits_data_product.pl -n metadata \
                                        -h db.pat.sdm.noao.edu \
                                        -u system_admin \
                                        -pass nsa_devel \
                                        -no_update_siap $base
done
