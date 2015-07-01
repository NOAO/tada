#! /usr/bin/env python3
' Create XML version of a FITS header.'

import sys
import argparse
import logging

import astropy.io.fits as pyfits

# To generate very rough XSD:
#   http://www.thaiopensource.com/relaxng/trang.html (best; install java)
#   http://xmlgrid.net/xml2xsd.html (online)

def fits_to_xml(fits_fname, xml_file):
    hdulist = pyfits.open(fits_fname)
    xmlstr = '<fitsHeader>\n'
    #!print('DBG: hdr={}'.format(hdulist[0].header.tostring()))
    hdr = hdulist[0].header
    for k,v in hdr.items():
        if k == '': 
            continue
        #print('k={}, v={}'.format(k,v))
        xmlstr += '  <{key}>{value}</{key}>\n'.format(key=k, value=v)
    xmlstr += '</fitsHeader>\n'
    print(xmlstr, file=xml_file)


##############################################################################

def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Output output')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.infile.close()
    args.infile = args.infile.name
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])
 
    fits_to_xml(args.infile, args.outfile)

if __name__ == '__main__':
    main()
        
    
