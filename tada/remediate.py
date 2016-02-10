#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import subprocess
import cmd
import readline
import os.path
import os
import shutil
import yaml
from datetime import datetime,date
import socket
from pathlib import PurePath
import astropy.io.fits as pyfits

from . import irods331 as iu
from . import file_naming as fn

def get_hdr_fname(fitsname):
    """Derive HDR filename from FITS filename"""
    return(fitsname.replace(fn.fits_extension(fitsname), 'hdr'))

# /noao-tuc-z1/mtn/20151006/...  =>  /noao-tuc-z1/mtn/REMEDTRASH/20151006/...
def move_archive_file_to_trash(fitsname):
    """Move Archive/Mass-store (fits,hdr) file out of the way 
and delete from DB in preparation for re-ingest"""
    archive331 =  '/noao-tuc-z1/mtn'

    # move irods files (fits, hdr) from standard location to /.../REMED/...
    trash_fits = fitsname.replace(archive331, archive331+'/REMEDTRASH')
    if not iu.irods_move331(fitsname, trash_fits):
        print('ERROR: Could not imv from {} to {}'
              .format(fitsname, trash_fits))
        return None
    hdrname = get_hdr_fname(fitsname)
    trash_hdr = hdrname.replace(archive331, archive331+'/REMEDTRASH')
    if not iu.irods_move331(hdrname, trash_hdr):
        print('ERROR: Could not imv from {} to {}'
              .format(hdrname, trash_hdr))
        return None

    # Delete from DB; see mars:perlport.drop_file(cursor, reference)
    print('Removed file but did NOT delete from DB: {}'
          .format(fitsname))
    
    
def get_from_archive(fitsname,
                     sandbox=os.path.expanduser('~/.tada/sandbox')):
    """Copy FITS and HDR files from mass-store to local sandbox using irods"""
    archive331 =  '/noao-tuc-z1/mtn'

    # get FITS
    local_fits = str(sandbox / PurePath(fitsname).relative_to(archive331))
    os.makedirs(os.path.dirname(local_fits), exist_ok=True)
    if not iu.irods_get331(fitsname, local_fits):
        print('ERROR: Could not iget from {} to {}'
              .format(fitsname, local_fits))
        return None

    # get HDR
    hdrname = get_hdr_fname(fitsname)
    local_hdr = str(sandbox / PurePath(hdrname).relative_to(archive331))
    if not iu.irods_get331(hdrname, local_hdr):
        print('ERROR: Could not iget from {} to {}'
              .format(hdrname, local_hdr))
        return None

    # Record what we did
    now = datetime.now().strftime('%m/%d/%y_%H:%M:%S')
    fixdata = dict(archivefits=fitsname,
                   archivehdr=hdrname,
                   retrieved=now,
                   sandbox=sandbox,
                   )
    yaml_fname = local_fits + '.fix.yaml'
    with open(yaml_fname, 'w') as yf:
        yaml.safe_dump(fixdata, yf, indent=4, width=20)

    logging.debug('get from irods to: {}, {}'.format(local_fits, local_hdr))
    return(local_fits, local_hdr)
    
def drop_dir(fitsdir):
    cmd = ('rsync -avz --password-file ~/.tada/rsync.pwd {}/ tada@{}::dropbox'
           .format(fitsdir, socket.getfqdn()))
    print('DBG-executing:{}'.format(cmd))
    print(subprocess.check_output(cmd, shell=True).decode('utf-8'))
    print('Submitted FITS files in: {}'.format(fitsdir))
    
class RepairShell(cmd.Cmd):
    intro = ('Welcome to the Archive remediation shell.'
             '   Type help or ? to list commands .\n')
    prompt = '(repair) '
    file = None
    manifest = '/var/log/tada/submit.manifest'
    sandboxdir = os.path.expanduser('~/.tada/sandbox')
    os.makedirs(sandboxdir, exist_ok=True)
    activeset = set()

    # ----- Remediation Work-flow commands --------
    def do_redo(self, arg):
        'Move everything from Inactive Queue to Active (re-submit)'
        subprocess.check_output(['dqcli', '--redo'])
        print(subprocess.check_output(['dqcli', '--summary']).decode('utf-8'))
    def do_get(self, arg):
        """Get files (FITS+HDR) from Archive and put in local sandbox. """
        fits_list = arg.split()
        for fits in fits_list:
            lfits,lhdr = get_from_archive(fits)
            if lfits:
                self.activeset.add(lfits)
            print('Saved 2 files: {}, {}'.format(lfits, lhdr))
    def do_trash(self, arg):
        """Move files in Mass Store to 'trash' (on mass store)"""
        fits_list = arg.split()
        for fits in fits_list:
            move_archive_file_to_trash(fits)
    def do_fix(self, arg):
        """Apply header changes to a FITS file.
fix <fitsfile> <key1=val1> [<key1=val1> ...]
"""
        fits,*p_list = arg.split()
        changes = parse_nv(p_list)
        changes['TADAFIX'] = ' '.join(p_list)
        #! print('fix(fits={}, changes={}'.format(fits, changes))
        today = date.today().isoformat().replace('-','')
        workingfits = os.path.join(self.sandboxdir, today, 'fix', 
                                   PurePath(fits).name)
        os.makedirs(os.path.dirname(workingfits), exist_ok=True)
        self.activeset.add(workingfits)
        shutil.copyfile(fits,workingfits)
        fixdata=dict(update=changes,
                     origfits=fits,
                     modifiedfits=workingfits,
                     )
        yaml_fname = workingfits + '.fix.yaml'
        with open(yaml_fname, 'w') as yf:
            yaml.safe_dump(fixdata, yf, indent=4, width=20)
        hdulist = pyfits.open(workingfits, mode='update') # modify IN PLACE
        fitshdr = hdulist[0].header # use only first in list.
        fitshdr.update(changes)
        hdulist.flush()
        hdulist.close()         # now FITS header is MODIFIED
        print('(Modified file written to: {}'.format(workingfits))
    def do_submit(self, arg):
        'Submit a FITS file to TADA for ingest.'
        drop_dir(self.sandboxdir)
    def do_header(self, arg):
        """Display FITS header.
header [<fitsfile>] 
fitsfile :: defaults to ACTIVE
"""
        fits = arg if len(arg) > 0 else list(self.activeset)[0]
        print(subprocess.check_output(['fitsheader', fits])
              .decode('utf-8'))
    def do_status(self, arg):
        """Get status of recent FITS file submission.
status <cnt>
  cnt :: Output last CNT records of Submit manifest."""
        cnt = int(arg) if len(arg) > 0 else 20
        print(subprocess.check_output('tail -{} {}'.format(cnt, self.manifest),
                                      shell=True).decode('utf-8'))
        print(subprocess.check_output(['dqcli']).decode('utf-8'))
        print('Active set={}'.format(self.activeset))
    def do_apply(self, arg):
        'Apply remediation recipe to list of FITS files.'
        logging.error('NOT IMPLEMENTED - not part of MVP')
    def do_shell(self, arg):
        'Run a unix shell command and display its ouput'
        print(subprocess.check_output(arg, shell=True).decode('utf-8'))
    def do_quit(self, arg):
        'Stop fixing things and exit'
        print('Exiting remediation work-flow')
        return True
    do_EOF=do_quit
    
def parse_nv(pair_list):
    'List name/value pairs ["n1=v1", "n2=v2"] to dict.'
    return(dict([p.split('=') for p in pair_list]))

def start_workflow():
    """The work-horse function."""
    RepairShell().cmdloop()
    



##############################################################################

def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    #!parser.add_argument('infile', type=argparse.FileType('r'),
    #!                    help='Input file')
    #!parser.add_argument('outfile', type=argparse.FileType('w'),
    #!                    help='Output output')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    #start_workflow(args.infile, args.outfile)
    start_workflow()

if __name__ == '__main__':
    main()


