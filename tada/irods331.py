"All use of iRODS by TADA is done through these functions"

import subprocess
import logging
import os
import os.path
import shutil
import tempfile

from . import utils as tut
from . import exceptions as tex

'''
From the icommands documentation:
The -T option will renew the socket connection between the client and 
server after 10 minutes of connection. This gets around the problem of
sockets getting timed out by the server firewall as reported by some users.
'''


def irods_init331():
    "Set irods password."
    logging.debug('irods_init331()'.format())
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    try:
        print('Enter your current iRODS password:')
        cmd = [os.path.join(icmdpath, 'iinit')]
        subprocess.check_output(cmd),
    except subprocess.CalledProcessError as ex:
        return False
    
    return True

        
def irods_setenv(host, port, resource):
    tag='irods_setenv'
    envDir = os.path.expanduser('~/.irods')
    pre_env = os.path.join(envDir,'.irodsEnv.pre-tada')
    irods_env = os.path.join(envDir,'.irodsEnv')
    post_env = os.path.join(envDir,'.irodsEnv.post-tada')
    os.makedirs(envDir, exist_ok=True)

    # Set password if it hasn't already been set
    #!if not os.path.exists(os.path.join(envDir,'.irodsA')):
    #!    irods_init331()
        
    if os.path.exists(irods_env):
        shutil.move(irods_env, pre_env)
        
    if os.path.exists(post_env):
        shutil.copy(post_env, irods_env)
    else:
        content='''
irodsHost {host}
irodsPort {port}
irodsUserName cache
irodsZone noao-tuc-z1
irodsDefResource {resource}
irodsHome /noao-tuc-z1/home/cache
irodsCwd /noao-tuc-z1/home/cache
    '''.format(host=host, port=port, resource=resource)
        with open(irods_env, 'w') as f:
            f.write(content)
        shutil.copy(irods_env, post_env)

def irods_put331(local_fname, irods_fname):
    "Copy local_fname to irods_fname, creating dirs if needed."
    tag='irods_put331'
    #!logging.debug('{}({}, {})'.format(tag, local_fname, irods_fname))
    #!logging.debug('   irods_put331 env:{})'.format(os.environ))
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    logging.debug('{}({}, {})'.format(tag, local_fname, irods_fname))
    tut.tic()
    (fd, temp_fname) = tempfile.mkstemp()
    os.close(fd)
    try:
        #!out = subprocess.check_output(os.path.join(icmdpath, 'ienv'))
        #!logging.debug('DBG-irods: ienv={}'.format(out))
        cmd = [os.path.join(icmdpath, 'imkdir'),
               '-p',
               os.path.dirname(irods_fname)]
        #!subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        #! start_new_session=True)
        cmd = [os.path.join(icmdpath, 'iput'),
               '-f', '-K',
               '--retries', '4', '-X', temp_fname,
               local_fname, irods_fname]
        #!subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        msg = ('icommand {} failed: {}; {}'
               .format(tag, ex, ex.output.decode('utf-8')))
        logging.error(msg)
        raise tex.FailedIrodsCommand(msg)
    finally:
        os.unlink(temp_fname)

    logging.debug('{} completed in {} seconds'.format(tag,tut.toc()))

def irods_get331(irods_fname, local_fname):
    "Copy irods_fname to local_fname."
    tag='irods_get331'
    logging.debug('{}({}, {})'.format(tag, irods_fname, local_fname))
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    try:
        # -f:: force overwrite of local file if it exists
        # -K:: verify checksum
        cmd = [os.path.join(icmdpath, 'iget'),
               '-f', '-K', irods_fname, local_fname]
        subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as ex:
        logging.debug('did not do {}: {}; {}'
                      .format(tag, ex, ex.output.decode('utf-8')))
        return False
    return True

def irods_move331(src_irods_fname, dst_irods_fname):
    "Move src_irods_fname to dst_irods_fname."
    tag='irods_move331'
    logging.debug('{}({}, {})'.format(tag, src_irods_fname, dst_irods_fname))
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    try:
        cmd = [os.path.join(icmdpath, 'imkdir'),
               '-p',
               os.path.dirname(dst_irods_fname)]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        subprocess.check_output(
            [os.path.join(icmdpath, 'imv'), src_irods_fname, dst_irods_fname],
            stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as ex:
        logging.debug('did not do {}: {}; {}'
                      .format(tag, ex, ex.output.decode('utf-8')))
        return False
    return True

def irods_remove331(irods_fname):
    "Remove irods_fname from irods"
    tag='irods_remove331'
    logging.debug('{}({})'.format(tag, irods_fname))
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    try:
        cmd = [os.path.join(icmdpath, 'irm'), '-f', irods_fname]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        msg = ('icommand "{}" failed: {}; {}'
               .format(tag, ex, ex.output.decode('utf-8')))
        logging.error(msg)
        raise tex.FailedIrodsCommand(msg)

def irods_exists331(irods_fname):
    "Find out if file already exists. RETURN: True if it does"
    tag='irods_exists331'
    logging.debug('{}({})'.format(tag, irods_fname))
    icmdpath = ('/usr/local/share/applications/irods3.3.1/iRODS/clients'
                '/icommands/bin')
    try:
        stat = subprocess.call([os.path.join(icmdpath, 'ils'),irods_fname],
                               stderr=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as ex:
        logging.error('FAILED {}: {}; {}'
                      .format(tag, ex, ex.output.decode('utf-8')))
        return False
    return (stat == 0)

    
