#! /usr/bin/env python3
import argparse
import logging
import yaml

from . import fits_utils as fu

def pers2yaml(pers_fname, yaml_fname):
    po, pp = fu.get_personality_dict(pers_fname)    
    #!if 'calchdr' in pp:
    #!    pp['calchdr'] = pp['calchdr'].split(',')
    data = dict(options=po, params=pp)
    with open(yaml_fname, 'w') as yf:
        #yaml.safe_dump(data, yf, indent=4, width=20)
        yaml.safe_dump(data, yf, default_flow_style=False)


##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Convert BASH style personality files to YAML format.',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('pfile',
                        help='Source personality (BASH) file')
    parser.add_argument('yfile',
                        help='Destination YAML file')
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


    pers2yaml(args.pfile, args.yfile)
    with open(args.yfile) as yf:
        dd = yaml.load(yf)
        #!print('dd={}'.format(dd))
if __name__ == '__main__':
    main()
