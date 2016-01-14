#! /usr/bin/env python3
"""When files appear in watched directory, push them to queue. This should be
wrapped into a service."""

import argparse
import logging
import os.path


import yaml


from . import config
from .monitors import push_drops


##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Ingest or stash files as the appear in watched directory',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dflt_config = '/etc/tada/tada.conf'
    logconf='/etc/tada/pop.yaml'
    parser.add_argument('--logconf',
                        help='Logging configuration file (YAML format).'
                        '[Default={}]'.format(logconf),
                        default=logconf,
                        type=argparse.FileType('r'))
    parser.add_argument('-c', '--config',
                        help='Config file. [default={}]'.format(dflt_config),
                        default=dflt_config,
                        )
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING',
                        )
    args = parser.parse_args()

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logdict = yaml.load(args.logconf)
    logging.config.dictConfig(logdict)
    logging.getLogger().setLevel(log_level)

    qcfg, dirs = config.get_config(None,
                                   validate=False,
                                   json_filename=args.config)
    push_drops(qcfg)

if __name__ == '__main__':
    main()
