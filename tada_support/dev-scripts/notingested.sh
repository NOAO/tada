#!/bin/bash


mapping=bok2.mapping
ingested=bok2.ingested

# head -3 $mapping $ingested
# ==> bok2.mapping <==
# ksb_150412_012529_zri.fits.fz produced from /data/bok2/20150411/d7124.0001.fits.fz
# ksb_150412_012606_zri.fits.fz produced from /data/bok2/20150411/d7124.0002.fits.fz
# ksb_150412_012643_zri.fits.fz produced from /data/bok2/20150411/d7124.0003.fits.fz
# 
# ==> bok2.ingested <==
# 
#  ksb_150412_012529_zri.fits.fz
#  ksb_150412_012606_zri.fits.fz

# wc -l $mapping $ingested
#   3786 bok2.mapping
#   3735 bok2.ingested

join -v 1 $mapping $ingested  | cut  -d' ' -f4 
