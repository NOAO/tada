#! /usr/bin/env python
"""Compare expected/actual audit counts from MARS (all hide=False records)
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import csv
from collections import Counter
import requests
from pprint import pprint,pformat

def compare_counts(expected=None,
                   marshost='mars1.sdm.noao.edu',
                   #secs to wait for any bytes
                   timeout=10 ):
    """The work-horse function."""
    uri='http://{}:8000/audit/unhidecnt/'.format(marshost)
    r = requests.get(uri, timeout=timeout)
    #print('svc response: \n{}'.format(pformat(r.json())))
    actual = r.json()
    #print('expected={}'.format(expected))
    errors = list() #  [(field, expected, actual), ...]
    ignore = ['loglevel', 'marshost', 'version']
    for k,v in expected.items():
        if k in ignore: continue
        if v == None:
            continue
        else:
            got = actual.get(k, '<none>')
            if v != got:
                errors.append((k,v,got))
    return errors
    



##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('--marshost', '-m',
                        #default='mars.vagrant.noao.edu',
                        default='mars1.sdm.noao.edu',   # env(MARSHOST)
                        help='MARS host that provides web-service for audit counts')
    parser.add_argument('--errcode_DUPFITS', type=int)
    parser.add_argument('--errcode_NOPROP', type=int)
    parser.add_argument('--success_True', type=int)
    parser.add_argument('--success_False', type=int)
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

    errors = compare_counts(marshost=args.marshost, expected=vars(args))
    if len(errors) > 0:
        print('errors(field,expected,actual)={}'.format(errors))
    else:
        print('Got expected results')
    sys.exit(len(errors))
    
if __name__ == '__main__':
    main()
