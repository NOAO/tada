"""Interface to working with irods.  All of our calls to irods
provided functions should be in this file."""

import os
import os.path
import subprocess
import logging
import tempfile

import tada.diag as diag

# imeta add -d /tempZone/mirror/vagrant/32/no_PROPID.fits x 1
# imeta set -d /tempZone/mirror/vagrant/32/no_PROPID.fits y 2
# imeta ls  -d /tempZone/mirror/vagrant/32/no_PROPID.fits
#
# isysmeta mod /tempZone/mirror/vagrant/32/no_PROPID.fits datatype 'FITS image'
# isysmeta ls -l /tempZone/mirror/vagrant/32/no_PROPID.fits 

# Get the pysical location
# iquest "%s" "select DATA_PATH where DATA_NAME = 'k4n_20141114_122626_oru.fits'"

def irods_get_physical(ipath):
    #!!! Open access to vault
    out = 'NONE'
    cmdline = ['iexecmd', 'open_vault.sh']
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise

    sel = ("select DATA_PATH where COLL_NAME = '{}' and DATA_NAME = '{}'"
           .format(os.path.dirname(ipath), os.path.basename(ipath)))
    cmdline = ['iquest', '"%s"', sel]
    out = 'NONE'
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    physical_fname = out.decode('utf-8').strip('\n \"')
    return physical_fname

def irods_debug():
    """For diagnostics only."""
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        cmdline = ['ienv']
        try:
            diag.dbgcmd(cmdline)
            out = subprocess.check_output(cmdline)
        except subprocess.CalledProcessError as ex:
            cmd = ' '.join(cmdline)
            logging.error('Execution failed: {}; {} => {}'
                          .format(ex, cmd, ex.output.decode('utf-8')))
            raise
        logging.debug('ienv={}'.format(out.decode('utf-8')))
    

# NB: The command must be installed in the server/bin/cmd directory
#     of the irods server
# e.g.
#     sudo cp /usr/bin/file_type /var/lib/irods/iRODS/server/bin/cmd/
def irods_file_type(irods_fname):
    logging.debug('irods_file_type({})'.format(irods_fname))

    # lut[file_type.py_key] = irods_data_type (list all using "isysmeta ldt")
    lut = dict(FITS = 'FITS image',
               JPEG = 'jpeg image',
               )
    cmdline = ['iexecmd', '-P', irods_fname, 'file_type {}'.format(irods_fname)]
    out = 'NONE'
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    typeStr = out.decode('utf-8')[:-1]

    # Set datatype in metadata. Not used. Retained for future use.
    #! dt = lut.get(typeStr,'generic')
    #! cmdline = ['isysmeta', 'mod', irods_fname, 'datatype', dt]
    #! try:
    #!     out = subprocess.check_output(cmdline)
    #! except subprocess.CalledProcessError as ex:
    #!     cmd = ' '.join(cmdline)
    #!     logging.error('Execution failed: {}; {} => {}'
    #!                   .format(ex, cmd, ex.output.decode('utf-8')))
    #!     raise

    return typeStr


def irods_set_meta(ifname, att_name, att_value):
    cmdline = ['imeta', 'set', '-d', ifname, 'prep', 'True']
    out = 'NONE'
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise


def irods_mv(src_ipath, dst_ipath):
    'Move/rename irods file' 
    logging.debug('irods_mv({}, {})'.format(src_ipath, dst_ipath))
    # imv /tempZone/mountain_mirror/vagrant/13/foo.nhs_2014_n14_299403.fits /tempZone/mountain_mirror/vagrant/13/nhs_2014_n14_299403.fits

    cmdline = ['imv', src_ipath, dst_ipath]
    out = None
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    return out

def irods_mv_tree(src_ipath, dst_ipath):
    'Move/rename irods file including parent directories' 
    logging.debug('irods_mv_tree({}, {})'.format(src_ipath, dst_ipath))
    # mv /tempZone/mirror/vagrant/13/foo.fits /tempZone/archive/vagrant/13/foo.fits
    try:
        subprocess.check_output(['imkdir', '-p',
                                 os.path.dirname(dst_ipath)])
        subprocess.check_output(['imv', src_ipath, dst_ipath])
    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'.format(ex, ex.output.decode('utf-8')))
        raise

 

#!# light-weight but dangerous.
#!# Register file in irods331  to physical file under irods403.
#!def fast_bridge_copy(src_ipath, dst_ipath, remove_orig=False):
#!    logging.warning(':Start EXECUTING FAST TEMP HACK!!!: bridge_copy({}, {})'
#!                    .format(src_ipath, dst_ipath))
#!    local_file = irods_get_physical(src_ipath)
#!    irods_reg_331(local_file, dst_ipath)
#!
#!    logging.warning(':Done EXECUTING FAST TEMP HACK!!!')
#!    return dst_ipath
#!    
#!# This does expensive iget, iput combination!!!
#!# When Archive moves up to irods 4, we can dispense with this nonsense!
#!def bridge_copy(src_ipath, dst_ipath, remove_orig=False): 
#!    logging.warning(':Start EXECUTING TEMPORARY HACK!!!: bridge_copy({}, {})'
#!                  .format(src_ipath, dst_ipath))
#!
#!    (fd, temp_fname) = tempfile.mkstemp()
#!    os.close(fd)
#!    cmdargs1 = ['iget', '-f', src_ipath, temp_fname]
#!    try:
#!        diag.dbgcmd(cmdargs1)
#!        subprocess.check_output(cmdargs1)
#!    except subprocess.CalledProcessError as ex:
#!        logging.error('Execution failed: {}; {}'
#!                      .format(ex,
#!                              ex.output.decode('utf-8')))
#!        raise
#!    logging.debug('Successful iget {} into {}'.format(src_ipath, temp_fname))
#!    irods_put331(temp_fname, dst_ipath)
#!    logging.debug('Successful put-331 {} into {}'.format(temp_fname, dst_ipath))
#!    os.unlink(temp_fname)
#!
#!    # Only happens if iget and iput succeed
#!    if remove_orig:
#!        cmdargs2 = ['irm', '-f', '-U', src_ipath]
#!        try:
#!            diag.dbgcmd(cmdargs2)
#!            subprocess.check_output(cmdargs2)
#!        except subprocess.CalledProcessError as ex:
#!            logging.error('Execution failed: {}; {}'
#!                          .format(ex, ex.output.decode('utf-8')))
#!            raise
#!        
#!    logging.debug(':Done EXECUTING TEMPORARY HACK!!!')
#!    return dst_ipath
#!


def irods_mv_dir(src_idir, dst_idir):
    """Move irods directory (collection) from one place to another,
creating desting parent directories if needed."""
    try:
        subprocess.check_output(['imkdir', '-p', dst_idir])
        subprocess.check_output(['imv', src_idir, dst_idir])
    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise

def irods_put(local_fname, irods_fname):
    'Put file to irods, creating parent directories if needed.'
    logging.debug('irods_put({}, {})'.format(local_fname, irods_fname))

    #os.chmod(local_fname, 0o664)
    try:
        subprocess.check_output(['imkdir', '-p',  os.path.dirname(irods_fname)])
        subprocess.check_output(['iput', '-f', '-K', local_fname, irods_fname])
        #! top_ipath = '/' + irods_fname.split('/')[1]
        #! subprocess.check_output(['ichmod', '-r', 'own', 'public', top_ipath])
    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise

def irods_get(local_fname, irods_fname, remove_irods=False):
    'Get file from irods, creating local parent directories if needed.'
    os.makedirs(os.path.dirname(local_fname), exist_ok=True)
    cmdargs1 = ['iget', '-f', '-K', irods_fname, local_fname]
    try:
        diag.dbgcmd(cmdargs1)
        subprocess.check_output(cmdargs1)
    except subprocess.CalledProcessError as ex:
        logging.error('Execution failed: {}; {}'
                      .format(ex, ex.output.decode('utf-8')))
        raise

    if remove_irods:
        cmdargs2 = ['irm', '-f', '-U', irods_fname]
        try:
            diag.dbgcmd(cmdargs2)
            subprocess.check_output(cmdargs2)
        except subprocess.CalledProcessError as ex:
            logging.error('Execution failed: {}; {}'
                          .format(ex, ex.output.decode('utf-8')))
            raise
    

def irods_unreg(irods_path):
    "unregister the file or collection"
    logging.warning('EXECUTING: "irm -U {}"; Remove need!!!'.format(irods_path))
    out = None
    cmdline = ['irm', '-U', irods_path]
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    return out

def irods_reg(fs_path, irods_path):
    """Register a file or a directory of files and subdirectory into
iRODS. The file must already exist on the server where the resource is
located. The full path must be supplied for both paths."""
    logging.warning('Use of iRODS "ireg" command SHOULD BE AVOIDED!')
    out = None
    cmdline = ['imkdir', '-p', os.path.dirname(irods_path)]
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise

    os.chmod(fs_path, 0o664)
    cmdline = ['ireg',  '-K', fs_path, irods_path]
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    return out

    
def get_irods_cksum(irods_path):
    cmdline = ['ichksum', irods_path]
    try:
        diag.dbgcmd(cmdline)
        out = subprocess.check_output(cmdline)
    except subprocess.CalledProcessError as ex:
        cmd = ' '.join(cmdline)
        logging.error('Execution failed: {}; {} => {}'
                      .format(ex, cmd, ex.output.decode('utf-8')))
        raise
    return(out.split()[1].decode('utf-8'))
