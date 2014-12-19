#! /usr/bin/env python
"""Fake version of Archive Ingest.  Read from TCP port and pretend to
store store a FITS file in the archive"""

import sys
import argparse
import logging
import socketserver
import functools

class MyTCPHandler(socketserver.StreamRequestHandler, outfile=None):
    """
    see: https://docs.python.org/3.4/library/socketserver.html#examples
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    self.outfile = outfile
     
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print("Mock archive ingest got data: ".format(self.data))
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data.upper())

def startup(host='127.0.0.1', port=8888, outfile='mock_ingest.out'):
    "Create the server, binding to host on port"
    server = socketserver.TCPServer(
        (host, port),
        functools.partial(MyTCPHandler, outfile=outfile)
    )

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument(--'host',
                        default='valley.test.noao.edu',
                        help='Ingest server host')
    parser.add_argument('--port',
                        default=6666,
                        type=int,
                        help='Ingest server port')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
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

    startup(host=args.host, port=args.port)

if __name__ == '__main__':
    main()
   
