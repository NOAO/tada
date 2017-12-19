#! /usr/bin/env python
"""Compare expected/actual log counts from MARS.
"""

import sys
import argparse
import logging
import csv
from collections import Counter
import requests
from pprint import pprint,pformat

def compare_counts(expected=None,
                   uri='http://localhost:8000/audit/marslogcnt/',
                   #secs to wait for any bytes
                   timeout=10 ):
    """The work-horse function."""
    print('logcnt uri={}'.format(uri))
    r = requests.get(uri, timeout=timeout)
    #print('svc response: \n{}'.format(pformat(r.json())))
    #print('expected={}'.format(expected))
    actual = r.json()
    errors = list() #  [(field, expected, actual), ...]
    ignore = ['loglevel', 'uri', 'version']
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
    parser.add_argument('--uri',
                  default='http://mars.vagrant.noao.edu:8000/audit/marslogcnt/',
                        help='MARS service that gives log counts')
    parser.add_argument('--ERROR', type=int)
    parser.add_argument('--INFO', type=int)
    parser.add_argument('--WARNING', type=int)
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

    errors = compare_counts(uri=args.uri, expected=vars(args))
    if len(errors) > 0:
        print('errors(field,expected,actual)={}'.format(errors))
    else:
        print('Got expected results')
    sys.exit(len(errors))
    
if __name__ == '__main__':
    main()
