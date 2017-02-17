#! /usr/bin/env python
"""Get stiLUT from MARS, store in YAML (for tada.settings via read on DQD startup)
"""

import sys
import argparse
import logging
import from_mars as fm

##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='Write YAML from web-service (JSON)',
        epilog='EXAMPLE: %(prog)s"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('--yamlfile', type=argparse.FileType('w'), default=sys.stdout,
                        help=('Output YAML file containing ProcType to Code map.'
                              ' [default=stdout]') )
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    fm.genProcTable(args.yamlfile)

if __name__ == '__main__':
    main()
