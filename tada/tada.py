#!/usr/bin/env python3
'TADA :: Telescope Automatic Data Archiver'

import sys
import string
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
        return False, 'Metadata keys could not be read. %s' % err

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

def getCandidateFiles(src_dir, delay=None):
    random.seed(15)
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            if not candidateFileP(fname):
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
- [ ] all of Thread-1
- [ ] insure minimum (level 0) set of required metadata fields in FITS
  + minimum acceptable for archive
- [ ] Test;  Verify all files in mock-IRODS contain required metadata
    '''

    def ingest(infile, archive_abs_path):
        shutil.copyfile(infile, archive_abs_path)

    for fname in getCandidateFiles(src_dir, delay=delay):
        base = os.path.basename(fname)
        ingest(fname, os.path.join(dst_dir, base))

    if verifyArchiveFilenamesP(src_dir, dst_dir):
        print('PASSED: thread2 archive contains expected filenames.')
    else:
        print('FAILED: thread2 archive DOES NOT contain expected filenames.')

    md_failures = set()
    for fname in getCandidateFiles(dst_dir, delay=None):
        ok, msg = validMetadataP(fname)
        if not ok:
            md_failures.add((fname,msg))

    if len(md_failures) == 0:
        print('PASSED: thread2 archive contains expected metadata.')
    else:
        print('%d files do not containg expected metadata: %s'
              % (len(md_failures), md_failures))
        print('FAILED: thread2 archive DOES NOT contain expected metadata'
              + ' in all files.')



##############################################################################

def main():
    default_end = 1e3
    parser = argparse.ArgumentParser(
        description='Move data from telescope instrument to archive',
        epilog='EXAMPLE: %(prog)s --loglevel=INFO --srcDir=/data/mtn cache --archiveDir=/data/archive'
        )
    parser.add_argument('--version', action='version',  version='0.0a1')
    parser.add_argument('--thread',
                        help='Which thread should be run',
                        type=int,
                        choices=[1, 2],
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
                        type=argparse.FileType('r') )
    parser.add_argument('--dfd', type=argparse.FileType('r'),
                        help='Graphviz (dot) file. Spec for DataFlow Diagram (network).')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING', 
                                 'INFO', 'DEBUG'],
                        default='WARNING',
                        )
    parser.add_argument('--srcDir', 
                        help='Directory containing source data files (images)',
                        )
    parser.add_argument('--archiveDir', 
                        help='Directory to treat as archive',
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

    assert os.path.isdir(args.srcDir), args.srcDir
    assert os.path.isdir(args.archiveDir), args.archiveDir

    if args.thread == 1:
        thread1(args.srcDir, args.archiveDir)
    elif args.thread == 2:
        thread2(args.srcDir, args.archiveDir)    

if __name__ == '__main__':
    main()
