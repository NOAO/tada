#!/bin/bash
# Update TADA tables from MARS and restart
# run as sudo

installTadaTables
service dqd restart

echo "TADA tables have been installed from MARS and dqd restarted."
