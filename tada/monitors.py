""""Monitor file additions to directorys and do something when then
happen.  On Linux 2.6 this uses inotify.  (Other platforms use
different underlying mechanisms which may be muc less efficient.)
"""

import os
import os.path
import logging
import shutil
import time
from pathlib import PurePath, Path
from glob import glob
import subprocess
import traceback

import yaml
import watchdog.events
import watchdog.observers

from . import submit as ts


##############################################################################
### Valley Monitor
###

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

If YAML files are found, they will be used for personalities.  

'''

def options_from_yamls(watched_path, ifname):
    """Returned combined options and parameters as single dict formed by 
collecting YAML files. Two locations will be looked in for YAML files:
  1. watched_path/<instrument>/*.yaml  (can be multiple)
  2. <ifname>.yaml                     (just one)
 """
    pdict = dict(options={}, params={})
    pdict['params']['filename'] = ifname # default 
    for yfile in sorted(glob(watched_path + '/*/*.yaml')):
        logging.debug('DBG: reading YAML {}'.format(yfile))
        with open(yfile) as yy:
            yd = yaml.safe_load(yy)
            pdict['params'].update(yd.get('params', {}))
            pdict['options'].update(yd.get('options', {}))

    yfile = ifname + '.yaml'
    if os.path.isfile(yfile):
        with open(yfile) as yy:
            yd = yaml.safe_load(yy)
            pdict['params'].update(yd.get('params', {}))
            pdict['options'].update(yd.get('options', {}))


    logging.debug('DBG: pdict={}'.format(pdict))
    
    return pdict 

class SubmitEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, watched_dir, rejected_dir, moddir, qcfg):
        self.watched_path = PurePath(watched_dir)
        self.rejected_path = PurePath(rejected_dir)
        self.moddir = moddir
        self.qcfg = qcfg
        super(watchdog.events.FileSystemEventHandler).__init__()

    def on_created(self, event):
        self.new_file(event.src_path)

    def on_moved(self, event):
        # for rsync: moved from tmp file to final filename
        self.new_file(event.dest_path)

    def new_file(self, ifname):
        pp = PurePath(ifname).relative_to(self.watched_path)
        if pp.suffix == '.fz' or pp.suffix == '.fits':
            logging.debug('Got FITS: {}'.format(ifname))
            pdict = options_from_yamls(str(self.watched_path), ifname)

            try:
                destfname = ts.protected_direct_submit(ifname, self.moddir,
                                                       personality=pdict,
                                                       qcfg=self.qcfg,
                                                       trace=True)
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
    """Ingest all files from dropbox into Archive"""
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
### Mountain Monitor
###
### We directory structure of watched_dir/<instrument>/<day> (YYYYMMDD) and
### for only a small subset of days to be changing. Therefore, it
### would be *better* if only the changing subset were watched.  But
### that's harder.  So, for now, recursively watch "watched_dir".
###

class PushEventHandler(watchdog.events.FileSystemEventHandler):
    """Copy new FITS file to CACHE and push to DQ.  If can't push, move 
to ANTICACHE."""
    def __init__(self, drop_dir, status_dir, qcfg):
        self.dropdir = drop_dir
        self.statusdir = status_dir
        self.cachedir= '/var/tada/cache'
        self.anticachedir= '/var/tada/anticache'
        super(watchdog.events.FileSystemEventHandler).__init__()

    def pushfile(self, fullfname):
        cmdstr = "md5sum {} | dqcli -q transfer --push  -".format(fullfname)
        subprocess.check_call(cmdstr, shell=True)

    def on_created(self, event):
        self.new_file(event.src_path)

    def on_moved(self, event):
        # for rsync: moved from tmp file to final filename
        self.new_file(event.dest_path)

    def on_modified(self, event):
        # So we can trigger event with "touch"
        self.new_file(event.src_path)

    def new_file(self, ifname):
        pp = PurePath(ifname).relative_to(PurePath(self.dropdir))
        if pp.suffix == '.fz' or pp.suffix == '.fits':
            logging.debug('push monitor got new file:{}'.format(ifname))
            try:
                cachename = ifname.replace(self.dropdir, self.cachedir)
                anticachename = ifname.replace(self.dropdir, self.anticachedir)
                statusname = ifname.replace(self.dropdir,
                                            self.statusdir)+'.status'
                logging.debug('DBG-2: Copy drop to cache={}'.format(cachename))
                os.makedirs(os.path.dirname(cachename), exist_ok=True)
                shutil.copy(ifname, cachename)
                # Combine all personalities into one and send that to valley.,
                pdict = options_from_yamls(self.dropdir, ifname)
                with open(cachename + '.yaml', 'w') as yf:
                    yaml.safe_dump(pdict, yf, width=50, indent=4)

                try:
                    self.pushfile(cachename)
                    logging.info('Pushed {} to mountain cache'
                                 .format(cachename))
                    os.makedirs(os.path.dirname(statusname), exist_ok=True)
                    Path(statusname).touch(exist_ok=True)
                except Exception as ex:
                    logging.error('Push FAILED with {}; {}'.format(ifname, ex))
                    logging.error(traceback.format_exc())
                    os.makedirs(os.path.dirname(anticachename), exist_ok=True)
                    shutil.move(cachename, anticachename)
            except Exception as ex:
                logging.error('PushEventHandler.new_file FAILED with {}; {}'
                              .format(ifname, ex))
                logging.error(traceback.format_exc())
            logging.debug('DBG-3: {}'.format(ifname))

def push_drops(qcfg):
    watched_dir = '/var/tada/dropbox'
    os.makedirs(watched_dir, exist_ok=True)
    status_dir = '/var/tada/statusbox'
    os.makedirs(status_dir, exist_ok=True)
    logging.info('Watching directory: {}'.format(watched_dir))

    handler = PushEventHandler(watched_dir, status_dir, qcfg)
    observer = watchdog.observers.Observer()
    observer.schedule(handler, watched_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
