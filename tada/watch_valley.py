#! /usr/bin/env python3
"""When files appear in watched directory, ingest them. This should be
wrapped into a service."""

import argparse
import logging
import os.path


import yaml


from . import config
from .monitors import ingest_drops


##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Ingest or stash files as the appear in watched directory',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dflt_moddir = os.path.expanduser('~/.tada/submitted')
    dflt_config = os.path.expanduser('~/.tada/config.json')
    logconf = os.path.expanduser('~/.tada/logging.yaml')
    parser.add_argument('watched_dir',
                        help='Try to ingest every file dropped into this '
                        'directory (or its subdirectories)')
    parser.add_argument('rejected_dir',
                        help='Move files that fail to ingest to this directory')
    parser.add_argument('-m', '--moddir',
                        help='Directory that will contain the (possibly '
                        'modified, possibly renamed) file as submitted. '
                        'Deleted after iRODS put. '
                        '[default={}]'.format(dflt_moddir),
                        default=dflt_moddir,
                        )
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
    logging.basicConfig(level = log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logdict = yaml.load(args.logconf)
    logging.config.dictConfig(logdict)
    logging.getLogger().setLevel(log_level)


    qcfg, dirs = config.get_config(None,
                                   validate=False,
                                   json_filename=args.config)
    ingest_drops(args.watched_dir, args.rejected_dir, args.moddir,
                 qcfg=qcfg)
if __name__ == '__main__':
    main()
