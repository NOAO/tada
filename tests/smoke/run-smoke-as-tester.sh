#!/bin/bash

su tester
source /opt/tada/venv/bin/activate
/opt/tada/tests/smoke/smoke.all.sh


# Add the following lines right below the pam_rootok.so line in your
# /etc/pam.d/su:
#
# auth       [success=ignore default=1] pam_succeed_if.so user = tester
# auth       sufficient   pam_succeed_if.so use_uid user = vagrant
