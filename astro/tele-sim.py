#! /usr/bin/env python3
'''\
Simulate "printing" of instrument data from telescope.
'''
# Docstrings intended for document generation via pydoc

import sys
import string
import argparse
import logging
import subprocess
import time
import random

def do_prints(filelist, delay_range=(0,1)):
    '''The work-horse function.'''

    args = 'lp -d astrorepo'.split()


    for file in filelist:
        seconds = random.uniform(delay_range[0], delay_range[1])
        logging.debug('Delay %s seconds before posting file' % (seconds,))
        time.sleep(seconds)
        out = subprocess.check_output(args+[file], universal_newlines=True)
        logging.info('Posted file: %s; %s' % (file,out))

##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version',  version='1.0.1')
    parser.add_argument('datafiles', nargs='*',
                        help='Data files')
    parser.add_argument('--cacheDir', 
                        help='Directory to contain mountain cache data files',
    )


    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING',
                        )
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
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled in %s !', sys.argv[0])

    do_prints(args.datafiles)

if __name__ == '__main__':
    main()
