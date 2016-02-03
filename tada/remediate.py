#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import subprocess
import cmd

class RepairShell(cmd.Cmd):
    intro = ('Welcome to the Archive remediation shell.'
             '   Type help or ? to list commands .\n')
    prompt = '(repair) '
    file = None

    # ----- Remediation Work-flow commands --------
    def do_retry(self):
        'Move everything from Inactive Queue to Active (re-submit)'
        subprocess.check_output(['dqcli', '--redo'])
        
    def do_change_header(self, *fits_list, **kwargs):
        'Apply header changes to a list of FITS files.'        
        logging.error('NOT IMPLEMENTED. '
                      'change_header(fits_list={}, changes={}'
                      .format(fits_list, kwargs))
    def do_submit(self,arg):
        'Submit a FITS file to TADA for ingest.'
        logging.error('NOT IMPLEMENTED - not part of MVP')
    def do_status(self,arg):
        'Get status of recent FITS file submission.'
        logging.error('NOT IMPLEMENTED - not part of MVP')
    def do_apply_recipe(self,arg):
        'Apply remediation recipe to list of FITS files.'
        logging.error('NOT IMPLEMENTED - not part of MVP')
    
def start_workflow(arg1, arg2):
    """The work-horse function."""
    return(arg1, arg2)



##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Output output')

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

    my_func(args.infile, args.outfile)

if __name__ == '__main__':
    main()


