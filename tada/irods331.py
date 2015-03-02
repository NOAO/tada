import subprocess
import logging
import os

def OLD_irods_put331(local_fname, irods_fname):
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
    
def irods_put331(local_fname, irods_fname):
    logging.debug('irods_put331({}, {})'.format(local_fname, irods_fname))
    logging.debug('   irods_put331 env:{})'.format(os.environ))
    #! os.environ.copy()
    #!env331 = dict(
    #!    irodsEnvFile = '/home/tada/.irods/.irodsEnv'        
    #!    )
    icmdpath='/usr/local/share/applications/irods3.3.1/iRODS/clients/icommands/bin'
    
    try:
        subprocess.check_output(['{}/imkdir'.format(icmdpath),
                                 '-p',  os.path.dirname(irods_fname)])
        subprocess.check_output(['{}/iput'.format(icmdpath),
                                 '-f', '-K', local_fname, irods_fname])

    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise
    
