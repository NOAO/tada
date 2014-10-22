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


def thread1(rawSrcDir, archiveDestDir, minDelay=.00, maxDelay=0.02):
    '''This is minimal "thread through the system" starting at raw-data
and terminating with files in the archive.  Input from rawSrcDir,
output to archiveDestDir.
- [ ] mock-LPR;  Feed each file in list to Ingest after specified delay
- [ ] Ingest;  Copy file into mock-IRODS (a local filesystem)
- [ ] Test;  Verify all input files are  in mock-IRODS
    '''
    def ingest(infile, archiveAbsolutePath):
        shutil.copyfile(infile, archiveAbsolutePath)

    logging.info('Copying files from "%s" to "%s"' % (rawSrcDir, archiveDestDir))
    random.seed(15)
    for root, dirs, files in os.walk(rawSrcDir):
        for fname in files:
            delay = random.uniform(minDelay,maxDelay)
            logging.info('  Archiving file "%s" to "%s" after %.2f seconds' % (rawSrcDir, archiveDestDir, delay))
            time.sleep(delay)
            ingest(os.path.join(root,fname), os.path.join(archiveDestDir,fname))

    # Verify
    lls = [files for r, d, files in os.walk(rawSrcDir)]
    lld = [files for r, d, files in os.walk(archiveDestDir)]
    origFiles = set(functools.reduce(operator.concat, 
                                     lls, 
                                     []))
    destFiles = set(functools.reduce(operator.concat, 
                                     lld, 
                                     []))
    missed = origFiles - destFiles
    if len(missed) > 0:
        print('ERROR: Not all files were archived! Missed: %s' % (missed,))
    else:
        print('SUCCESS: thread1 past test')


##############################################################################

def main():
    default_end = 1e3
    parser = argparse.ArgumentParser(
        description='Move data from telescope instrument to archive',
        epilog='EXAMPLE: %(prog)s --loglevel=INFO --srcDir=/data/mtn cache --archiveDir=/data/archive'
        )
    parser.add_argument('--version', action='version',  version='0.0a1')
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--end',
                        help='Time (seconds) to end simulation [default=%s]'
                        %(default_end),
                        type = int,
                        default = default_end,)
    parser.add_argument('--summarize',
                        default=[],
                        action='append')
    parser.add_argument('--cfg',
                        help='Configuration file',
                        type=argparse.FileType('r') )
    parser.add_argument('--dfd', type=argparse.FileType('r'),
                        help='Graphviz (dot) file. Spec for DataFlow Diagram (network).')

    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
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
    thread1(args.srcDir, args.archiveDir)
    

if __name__ == '__main__':
    main()
