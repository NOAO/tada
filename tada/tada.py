#!/usr/bin/env python3
'TADA :: Telescope Automatic Data Archiver'

import sys
import argparse
import logging

import simpy
import os
import shutil
import random
import time
import functools
import operator
import fnmatch
import pyfits
import subprocess
import icmd

def validMetadataP(fits):
    requiredFitsFields = set([
        'DATE-OBS',
        'DTACQNAM',
        'DTINSTRU',
        'DTNSANAM',
        'DTPI',
        'DTSITE',
        'DTSITE',
        'DTTELESC',
        'DTTITLE',
        'DTUTC',
        'PROPID',
    ])
    try:
        hdu = pyfits.open(fits)[0] # can be compressed
        hdr_keys = set(hdu.header.keys())
    except Exception as err:
        return False, 'Metadata keys could not be read: %s' % err

    missing = sorted(requiredFitsFields - hdr_keys)
    if len(missing) > 0:
        return (False,
                'FITS file is missing required metadata keys: %s'
                % (missing,))
    return True, None


def verifyArchiveFilenamesP(src_dir, dst_dir):
    # Verify
    lls = [files for r, d, files in os.walk(src_dir)]
    lld = [files for r, d, files in os.walk(dst_dir)]
    orig_files = set([f for f in functools.reduce(operator.concat, lls, [])
                      if candidateFileP(f)])
    dest_files = set(functools.reduce(operator.concat, lld, []))
    missed = orig_files - dest_files
    if len(missed) > 0:
        logging.info('Files not transfered:: %s' % (missed,))
        logging.info('FAILED: Not all files were archived!')
        return False, '%d files not transferred' % len(missed)
    else:
        return True, None

def candidateFileP(filename):
    return fnmatch.fnmatch(filename,'*.fits.fz')

def allFileP(filename):
    return True

# /dtskp_noaocache_mtn/20140921/kp4m/2014B-0461/k4k_140921_235746_zri.fits.fz
def getCandidateFiles(src_dir, delay=None, filterP=candidateFileP):
    'Yield successive absolute paths of files matching filterP'
    random.seed(15)
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            if not filterP(fname):
                continue
            if delay != None:
                seconds = random.uniform(delay[0], delay[1])
                logging.debug('Delay file get %.2f seconds' % (seconds,))
                time.sleep(seconds)
            yield os.path.join(root, fname)


def thread1(src_dir, dst_dir, delay=(.00, 0.02)):
    '''This is minimal "thread through the system" starting at raw-data
and terminating with files in the archive.  Input from src_dir,
output to dst_dir.
- [ ] mock-LPR;  Feed each file in list to Ingest after specified delay
- [ ] Ingest;  Copy file into mock-IRODS (a local filesystem)
- [ ] Test;  Verify all input files are  in mock-IRODS
    '''
    def ingest(infile, archive_abs_path):
        shutil.copyfile(infile, archive_abs_path)

    logging.info('Copying files from "%s" to "%s"' % (src_dir, dst_dir))
    for fname in getCandidateFiles(src_dir, delay=delay):
        logging.debug('  Ingest file "%s" to "%s" after %s seconds'
                      % (fname, dst_dir, delay))
        base = os.path.basename(fname)
        ingest(fname, os.path.join(dst_dir, base))

    if verifyArchiveFilenamesP(src_dir, dst_dir):
        print('PASSED: thread1 archive matches expected results.')
    else:
        print('FAILED: thread1 archive does NOT MATCH expected results.')

def thread2(src_dir, dst_dir, delay=None):
    '''Touches FITS data (verifies selected metadata in archive)
- [X] all of Thread-1
- [X] only transfer files matchin: *.fits.fz 
- [X] insure minimum (level 0) set of required metadata fields in FITS
  + minimum acceptable for archive
- On inadequate metadata:
  - [X] reject (don't archive) 
  - [ ] move to remediation store
  - [ ] log error
- [X] Test;  Verify all files in mock-IRODS contain required metadata;
    '''

    def ingest(infile, archive_abs_path):
        shutil.copyfile(infile, archive_abs_path)

    for fname in getCandidateFiles(src_dir, delay=delay):
        ok, msg = validMetadataP(fname)
        if ok:
            base = os.path.basename(fname)
            ingest(fname, os.path.join(dst_dir, base))
        else:
            logging.warning(('File "%s" did not contain expected metadata. '
                            +'NOT INGESTING: %s')
                            % (fname, msg))

    if verifyArchiveFilenamesP(src_dir, dst_dir):
        print('PASSED: thread2 archive contains expected filenames.')
    else:
        print('FAILED: thread2 archive DOES NOT contain expected filenames.')


def transfer_via_iput_list(ienv, src_path, irods_path, delay=None):        
    src_files = list(getCandidateFiles(src_path, delay=delay, filterP=allFileP))
    logging.debug('Transfer %d files via single iput' % (len(src_files)))
    if len(src_files) > 0:
        ienv.iput('-f',src_files, irods_path)
    return src_files

def transfer_via_iput_single(ienv, src_path, irods_path, delay=None):        
    src_files = []
    for fname in getCandidateFiles(src_path, delay=delay):
        assert fname.index(src_path) == 0
        tail = fname[len(src_path):]
        ienv.imkdir(os.path.dirname(irods_path+tail))
        ienv.iput('-f', [fname], irods_path+tail)
        src_files.append(fname)
    return src_files

def transfer_via_irsync(ienv, src_path, irods_path, delay=None):        
    ienv.irsync('-r',   # recursive
                '-s',   # use the size instead of the checksum value
                        # for determining  synchronization.
                # '-K', # calc and verify checksum
                src_dir, 'i:'+irods_path)

def transfer_via_rsync(src_path, mirror_path):
    subprocess.check_call(['rsync', '-r',
                           src_path,
                           #'rsync://valley.test.noao.edu/'+mirror_path
                           'vagrant@valley.test.noao.edu:'+mirror_path
                       ])
                          

# The src_dir serves as cache. Remove files from it after transfer to
# archive has been confirmed!!!
# TODO: Do in batches.  Let delay and yield work together!!!
def thread3(src_dir, irods_path, mirror_dir, archive_dir,
                   delay=None,
                   irodsHost='172.16.1.12',
                   irodsPort='1247',
                   irodsUserName='rods',
                   irodsZone='tempZone',
               ):
    logging.debug('THREAD-3: '
                  +'src_dir=%s, irods_path=%s, mirror_dir=%s, archive_dir=%s', 
                  src_dir, irods_path, mirror_dir, archive_dir)
    ienv = icmd.Icommands(host=irodsHost, port=irodsPort,
                          user_name=irodsUserName,
                          zone=irodsZone)


    ienv.imkdir(irods_path)

    #! transfer_via_iput_list(ienv, src_dir, irods_path, delay=delay)
    #! transfer_via_irsync(src_path, irods_path, delay=None):                
    # Both yields
    #   ERROR: connectToRhostPortal: connectTo Rhost 127.0.0.1 port 20069 error, status = -305111
    
    #!transfer_via_iput_single(ienv, src_dir, irods_path, delay=delay)
    transfer_via_rsync(src_dir, mirror_dir)

    

##############################################################################

def main():
    'Main driver with argument parsing'
    default_end = 1e3
    parser = argparse.ArgumentParser(
        description='Move data from telescope instrument to archive',
        epilog='EXAMPLE: %(prog)s --loglevel=INFO '
        + '--srcDir=/data/mtn cache --archiveDir=/data/archive'
        )
    parser.add_argument('--version', action='version', version='0.0a2')
    parser.add_argument('--thread',
                        help='Which thread should be run',
                        type=int,
                        choices=[1, 2, 3],
                        default=1
                        )
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--end',
                        help='Time (seconds) to end simulation [default=%s]'
                        %(default_end),
                        type=int,
                        default=default_end,)
    parser.add_argument('--summarize',
                        default=[],
                        action='append')
    parser.add_argument('--cfg',
                        help='Configuration file',
                        type=argparse.FileType('r'))
    parser.add_argument('--dfd', type=argparse.FileType('r'),
                        help='Graphviz (dot) file. '
                        + 'Spec for DataFlow Diagram (network).')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING',
                        )
    parser.add_argument('--cacheDir', 
                        help='Directory containing mountain cache data files (images)',
                        )
    parser.add_argument('--mirrorDir', 
                        help='Directory to treat as mirror',
                        )
    parser.add_argument('--archiveDir', 
                        help='Directory to treat as archive',
                        )
    parser.add_argument('--irodsPath',
                        default='/tempZone/valley',
                        help='iRODS collection to receive Mountain files',
                        )



    args = parser.parse_args()
    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    if args.cfg:
        cfg = json.load(args.cfg)

    # env = simpy.Environment()
    # G = setupDataflowNetwork(env, args.infile, profile=args.profile)
    # 
    # if args.loglevel == 'DEBUG':
    #     printGraphSummary(G)
    # 
    # env.run(until=args.end)
    # print_summary(env, G, summarizeNodes=args.summarize)

    assert os.path.isdir(args.cacheDir), args.cacheDir
    assert os.path.isdir(args.mirrorDir), args.mirrorDir


    if args.thread == 1:
        thread1(args.cacheDir, args.irodsPath, args.mirrorDir)
    elif args.thread == 2:
        thread2(args.cacheDir, args.irodsPath, args.mirrorDir)    
    elif args.thread == 3:
        thread3(args.cacheDir,
                args.irodsPath,
                args.mirrorDir,
                args.archiveDir)    

if __name__ == '__main__':
    main()
