#! /usr/bin/env python3
import argparse
import logging
import yaml
import shutil

from . import fits_utils as fu

def yaml2yaml(yamlfile):
    bu = yamlfile + ".bak"
    shutil.copy(yamlfile, bu)
    with open(yamlfile) as yy:
        yd = yaml.safe_load(yy)
                
    with open(yamlfile, 'w') as yf:
        yaml.dump(yd, yf, default_flow_style=False)


##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Convert BASH style personality files to YAML format.',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('yamlfile',
                        nargs='+',
                        help='YAML file to reformat (create *.bak duplicate of orig)')
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

    for yfile in args.yamlfile:
        print('Reformatting yaml file: {}'.format(yfile))
        yaml2yaml(yfile)

if __name__ == '__main__':
    main()
