# Collect the names of hosts that are needed for smoke tests.


ARCHHOST=`grep arch_host /etc/tada/hiera.yaml | cut -d' ' -f2`
IRODSHOST=`grep irods_host /etc/tada/hiera.yaml | cut -d' ' -f2`
DQHOST=`grep dq_host /etc/tada/hiera.yaml | cut -d' ' -f2`

MARSHOST=`grep mars_host /etc/tada/hiera.yaml | cut -d' ' -f2`
VALHOST=`grep valley_host /etc/tada/hiera.yaml | cut -d' ' -f2`

# There could be multiple mtns feeding one valley.  But for testing, its 1-to-1.
MTNHOST="mountain.vagrant.noao.edu"

