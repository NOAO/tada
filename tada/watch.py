#! /usr/bin/env python3
"""When files appear in watched directory, ingest them. This should be
wrapped into a service."""

import argparse
import logging
import os
import os.path
import random
import time
import shutil
from pathlib import PurePath
from glob import glob

import yaml

import watchdog.events
import watchdog.observers

from . import submit as ts
from . import config

'''
Expected directory structures:
/.../dropbox/
  instrument1/...
  instrument2/...
  ...

/.../valley-stash/
  ingested/instrument1/...
  rejected/instrument1/...

To submit a batch (e.g. for pipeline or new instrument):
  rsync -az ~/myfiles/newinstrument /.../dropbox/newinstrument

If YAML files are found, they will be used for personalities.  For each new fits file,
two locations will be looked in for YAML files: 
  /.../dropbox/<instrument>/*.yaml
  /.../dropbox/<instrument>/.../<terminal_dir>/*.yaml

'''



def fake_submit(ifname, checksum, qname, qcfg):
    pfail = 0.5
    r = random.random()
    if  r < pfail:
        raise Exception('FAILED')
    return ifname


class SubmitEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, watched_dir, rejected_dir, moddir, qcfg):
        self.watched_path = PurePath(watched_dir)
        self.rejected_path = PurePath(rejected_dir)
        self.moddir = moddir
        self.qcfg = qcfg
        super(watchdog.events.FileSystemEventHandler).__init__()
        
    def on_created(self,event):
        self.new_file(event.src_path)
    def on_moved(self,event):
        # for rsync: moved from tmp file to final filename
        self.new_file(event.dest_path)

    def new_file(self, ifname):
        p = PurePath(ifname).relative_to(self.watched_path)
        parts=p.parts
        logging.debug('DBG: new_file: ifname={},parts={}'.format(ifname, parts))

        #if isinstance(event, watchdog.events.FileCreatedEvent):
        if p.suffix == '.fz' or p.suffix == '.fits':
            logging.debug('Got FITS: {}'.format(ifname))
            pdir = self.watched_path / p.parts[0] / p.parts[1]
            logging.debug('DBG: pdir={}'.format(pdir))

            pdict = dict(options={}, params={})
            for yfile in sorted(glob(str(pdir) + '/' + '*.yaml')):
                logging.debug('DBG: reading YAML {}'.format(yfile))
                with open(yfile) as yy:
                    yd = yaml.safe_load(yy)
                    pdict['params'].update(yd.get('params',{}))
                    pdict['options'].update(yd.get('options',{}))

            destfname = str(self.rejected_path / p)
            yfile = ifname + '.yaml'
            if os.path.isfile(yfile):
                logging.debug('DBG: reading YAML {}'.format(yfile))
                with open(yfile) as yy:
                    yd = yaml.safe_load(yy)
                    pdict['params'].update(yd.get('params',{}))
                    pdict['options'].update(yd.get('options',{}))
            pdict['params']['calchdr'] = ','.join(pdict['params'].get('calchdr',[]))
            
            logging.debug('DBG: pdict={}'.format(pdict))
            try:
                #!fake_submit(ifname, 'checksum', 'qname', 'qcfg')
                destfname = ts.direct_submit(ifname, self.moddir,
                                             personality=pdict,
                                             qcfg=self.qcfg, trace=True)
            except Exception as sex:
                # FAILURE: stash it
                logging.info('Ingest FAILED: stash into: {}; {}'
                              .format(destfname, sex))
                os.makedirs(os.path.dirname(destfname), exist_ok=True)
                shutil.move(ifname, destfname)
            else:
                # SUCCESS: remove it
                logging.info('Ingest SUCCEEDED: remove: {}'.format(ifname))
                os.remove(ifname)
        
                
def ingest_drops(watched_dir, rejected_dir, moddir, qcfg):
    handler = SubmitEventHandler(watched_dir, rejected_dir, moddir, qcfg)
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
    dflt_moddir = os.path.expanduser('~/.tada/submitted')
    dflt_config = os.path.expanduser('~/.tada/config.json')
    logconf = os.path.expanduser('~/.tada/logging.yaml')
    parser.add_argument('watched_dir',
                        help='Try to ingest every file dropped into this '
                        'directory (or its subdirectories)')
    parser.add_argument('rejected_dir',
                        help='Move files that fail to ingest to this directory')
    parser.add_argument('-m', '--moddir',
                        default=dflt_moddir,
                        help="Directory that will contain the (possibly modified, possibly renamed) file as submitted. Deleted after iRODS put. [default={}]".format(dflt_moddir),
                        )
    parser.add_argument('--logconf',
                        help='Logging configuration file (YAML format).'
                        '[Default={}]'.format(logconf),
                        default=logconf,
                        type=argparse.FileType('r'))
    parser.add_argument('-c', '--config',
                        default=dflt_config,
                        help='Config file. [default={}]'.format(dflt_config),
                        )
    parser.add_argument('-t', '--timeout',
                        type=int,
                        help='Seconds to wait for Archive to respond',
                        )
    parser.add_argument('--trace',
                        action='store_true',
                        help='Produce stack trace on error')
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
    logDict = yaml.load(args.logconf)
    logging.config.dictConfig(logDict)
    logging.getLogger().setLevel(log_level)


    qcfg, dirs = config.get_config(None,
                                   validate=False,
                                   json_filename=args.config)
    ingest_drops(args.watched_dir, args.rejected_dir, args.moddir, qcfg=qcfg)
if __name__ == '__main__':
    main()
