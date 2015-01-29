import subprocess
import logging

def irods_put331(local_fname, irods_fname):
    logging.debug('irods_put331({}, {})'.format(local_fname, irods_fname))
    
    try:
        subprocess.check_output(
            ['/sandbox/tada/scripts/iput331 {} {}'
             .format(local_fname, irods_fname)],
            stderr=subprocess.STDOUT,
            shell=True)
    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise
    
