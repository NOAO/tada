#! /usr/bin/env python3
"""When files appear in watched directory, ingest them. This should be
wrapped into a service."""

'''
TODO:
- YAML for personality files
'''

import argparse
import logging
import os
import random
import time
import shutil
from pathlib import PurePath

import yaml

import watchdog.events
import watchdog.observers

from . import submit as ts


def fake_submit(ifname, checksum, qname, qcfg):
    pfail = 0.5
    r = random.random()
    if  r < pfail:
        raise Exception('FAILED')
    return ifname

def new_fits(ifname, watched_path, rejected_path, dest_path=None):
    p = PurePath(ifname).relative_to(watched_path)
    logging.debug('DBG: new_fits: ifname={}, p={}'
                  .format(ifname, str(p)))
    #if isinstance(event, watchdog.events.FileCreatedEvent):
    if p.suffix == '.fz' or p.suffix == '.fits':
        logging.debug('Got FITS: {}'.format(ifname))
        destfname=str(rejected_path / p)
        try:
            #destfname = ts.submit_to_archive(ifname, checksum, 
            #                                 qname, qcfg)
            fake_submit(ifname, 'checksum', 'qname', 'qcfg')
        except Exception as sex:
            # FAILURE: stash it
            logging.debug('Ingest FAILED: stash into: {}'
                          .format(destfname))
            shutil.move(ifname, destfname)
        else:
            # SUCCESS: remove it
            logging.debug('Ingest SUCCEEDED: remove: {}'.format(ifname))
            os.remove(ifname)
    

class SubmitEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, watched_dir, rejected_dir):
        self.watched_path = PurePath(watched_dir)
        self.rejected_path = PurePath(rejected_dir)
        super(watchdog.events.FileSystemEventHandler).__init__()
        
    def on_created(self,event):
        new_fits(event.src_path, self.watched_path, self.rejected_path)
    def on_moved(self,event):
        # for rsync: moved from tmp file to final filename
        new_fits(event.dest_path, self.watched_path, self.rejected_path)
                
def ingest_drops(watched_dir, rejected_dir):
    handler = SubmitEventHandler(watched_dir, rejected_dir)
    observer = watchdog.observers.Observer()
    logging.info('Watching directory: {}'.format(watched_dir))
    observer.schedule(handler, watched_dir, recursive=True)
    logging.debug('dbg: starting')
    observer.start()
    logging.debug('dbg: Started')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()    

##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Ingest or stash files as the appear in watched directory',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('watched_dir',
                        help='Try to ingest every file dropped into this '
                        'directory (or its subdirectories)')
    parser.add_argument('rejected_dir',
                        help='Move files that fail to ingest to this directory')
    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
                        choices = ['CRTICAL','ERROR','WARNING','INFO','DEBUG'],
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
    logging.debug('Debug output is enabled!!!')


    ingest_drops(args.watched_dir, args.rejected_dir)
if __name__ == '__main__':
    main()
