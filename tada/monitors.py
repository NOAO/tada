""""Monitor file additions to directorys and do something when then happen"""

import os
import os.path
import logging
import shutil
import time
from pathlib import PurePath
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
    for yfile in sorted(glob(watched_path + '/*/*.yaml')):
        logging.debug('DBG: reading YAML {}'.format(yfile))
        with open(yfile) as yy:
            yd = yaml.safe_load(yy)
            pdict['params'].update(yd.get('params', {}))
            pdict['options'].update(yd.get('options', {}))

    yfile = ifname + '.yaml'
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
        parts = pp.parts
        #logging.debug('DBG: new_file: ifname={},parts={}'.format(ifname, parts))

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

class PushEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, watched_dir, qcfg):
        self.watched_path = PurePath(watched_dir)
        self.destroot = qcfg['transfer']['cache_dir']
        super(watchdog.events.FileSystemEventHandler).__init__()

    def pushfile(self, fullfname):
        #destfname = fullfname.replace(str(self.watched_path), self.destroot)
        #os.makedirs(os.path.dirname(destfname), exist_ok=True)
        #shutil.move(fullfname, destfname)
        #cmdstr = "md5sum {} | dqcli -q transfer --push  -".format(destfname)
        cmdstr = "md5sum {} | dqcli -q transfer --push  -".format(fullfname)
        subprocess.check_call(cmdstr, shell=True)

    def on_created(self, event):
        self.new_file(event.src_path)

    def on_moved(self, event):
        # for rsync: moved from tmp file to final filename
        self.new_file(event.dest_path)

    def new_file(self, ifname):
        pp = PurePath(ifname).relative_to(self.watched_path)
        if pp.suffix == '.fz' or pp.suffix == '.fits':
            # Combine all personalities into one and send that to valley.,
            pdict = options_from_yamls(str(self.watched_path), ifname)
            with open(ifname + '.yaml', 'w') as yf:
                yaml.safe_dump(pdict, yf, width=50, indent=4)

            try:
                self.pushfile(ifname)
            except Exception as ex:
                traceback.print_exc()
                logging.error('Pop FAILED with {}; {}'.format(ifname, ex))
        

def push_drops(qcfg):
    watched_dir = os.path.join(qcfg['transfer']['cache_dir'],'dropbox')
    os.makedirs(watched_dir, exist_ok=True)
    logging.info('Watching directory: {}'.format(watched_dir))

    handler = PushEventHandler(watched_dir, qcfg)
    observer = watchdog.observers.Observer()
    observer.schedule(handler, watched_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
