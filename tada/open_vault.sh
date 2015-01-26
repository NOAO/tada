#!/bin/sh

# Close the vault part-way!!!
# We really only need to grant complete access to the process running tada.
# When the dust settles and we have a standard TADA group:
#   chgrp and grant rwX group access to vault
chmod --recursive ugo+rwX /var/lib/irods/iRODS/Vault
