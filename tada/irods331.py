"All use of iRODS by TADA is done through these functions"

import subprocess
import logging
import os

#! def OLD_irods_put331(local_fname, irods_fname):
#!     logging.debug('irods_put331({}, {})'.format(local_fname, irods_fname))
#!     
#!     try:
#!         subprocess.check_output(
#!             ['/sandbox/tada/scripts/iput331 {} {}'
#!              .format(local_fname, irods_fname)],
#!             stderr=subprocess.STDOUT,
#!             shell=True)
#!     except subprocess.CalledProcessError as ex:
#!         logging.error('Execution failed: {}; {}'
#!                       .format(ex, ex.output.decode('utf-8')))
#!         raise

def irods_put331(local_fname, irods_fname):
    "Copy local_fname to irods_fname, creating dirs if needed."
    logging.debug('irods_put331({}, {})'.format(local_fname, irods_fname))
    logging.debug('   irods_put331 env:{})'.format(os.environ))
    icmdpath = '/usr/local/share/applications/irods3.3.1/iRODS/clients/icommands/bin'
    cmd1 = '{}/imkdir -p {}'.format(icmdpath, os.path.dirname(irods_fname))
    try:
        subprocess.check_output(['su', '-', 'tada', '-c', cmd1])
        subprocess.check_output([os.path.join(icmdpath, 'iput'),
                                 '-f', '-K', local_fname, irods_fname])

    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise
