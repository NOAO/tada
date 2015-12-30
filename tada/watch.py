#! /usr/bin/env python3
"""When files appear in watched directory, ingest them. This should be
wrapped into a service."""

import argparse
import logging
import os
import random
import time
import shutil
from pathlib import PurePath

#from . import submit as ts
#import submit as ts

import watchdog.events
import watchdog.observers

def fake_submit(ifname, checksum, qname, qcfg):
    pfail = 0.5
    r = random.random()
    logging.debug('r={}'.format(r))
    if  r < pfail:
        raise Exception('FAILED')
    return ifname

class DropEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, watched_dir, rejected_dir):
        self.watched_path = PurePath(watched_dir)
        self.rejected_path = PurePath(rejected_dir)
        super(watchdog.events.FileSystemEventHandler).__init__()
        
    def on_created(self,event):
        if isinstance(event, watchdog.events.FileCreatedEvent):
            ifname=event.src_path
            p = PurePath(ifname).relative_to(self.watched_path)
            destfname=str(self.rejected_path / p)
            try:
                #destfname = ts.submit_to_archive(ifname, checksum, qname, qcfg)
                fake_submit(ifname, 'checksum', 'qname', 'qcfg')
            except Exception as sex:
                # FAILURE: stash it
                logging.debug('Ingest FAILED: stash into: {}'.format(destfname))
                shutil.move(event.src_path, destfname)
            else:
                # SUCCESS: remove it
                logging.debug('Ingest SUCCEEDED: remove: {}'
                              .format(event.src_path))
                os.remove(ifname)
                
def ingest_drops(watched_dir, rejected_dir):
    handler = DropEventHandler(watched_dir, rejected_dir)
    observer = watchdog.observers.Observer()
    observer.schedule(handler, watched_dir, recursive=True)
    observer.start()
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
