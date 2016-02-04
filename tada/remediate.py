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
import datetime
import socket
from pathlib import PurePath
import astropy.io.fits as pyfits

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
    stagedir = os.path.expanduser('~/.tada/stage')
    os.makedirs(stagedir, exist_ok=True)
    activeset = set()

    # ----- Remediation Work-flow commands --------
    def do_redo(self, arg):
        'Move everything from Inactive Queue to Active (re-submit)'
        subprocess.check_output(['dqcli', '--redo'])
        print(subprocess.check_output(['dqcli', '--summary']).decode('utf-8'))
    def do_fix(self, arg):
        """Apply header changes to a FITS file.
fix <fitsfile> <key1=val1> [<key1=val1> ...]
"""
        fits,*p_list = arg.split()
        changes = parse_nv(p_list)
        #! print('fix(fits={}, changes={}'.format(fits, changes))
        today = datetime.date.today().isoformat().replace('-','')
        workingfits = os.path.join(self.stagedir, today, 'fix', 
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
        drop_dir(self.stagedir)
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


