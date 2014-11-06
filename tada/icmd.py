#!/usr/bin/env python3
'''Interface to subset of irods icommands (http://irods.org/documentation/).'''

import logging
import subprocess
import os.path
import os

class IcommandException(Exception):
    pass
    

class Icommands():
    def __init__(self,
                 host='172.16.1.12', # valley
                 port='1247',
                 user_name='rods',
                 zone='tempZone',
                 ):
        self.host      = '172.16.1.12'
        self.port      = '1247'
        self.user_name = user_name
        self.zone      = zone
        self.cmds  = set('iput iget imkdir irsync ils'.split())

        self.env = os.environ.copy()
        #self.env['irodsEnvFile'] = '/path/to/desired/file'
        #self.env['irodsAuthFileName'] = '/path/to/desired/other/file'
        self.env['irodsHost'] = host
        self.env['irodsPort'] = port
        self.env['irodsUserName'] = user_name
        self.env['irodsZone'] = zone
        
                 
    def run_icmd(self, icmd, arg_list=None):
        if icmd not in self.cmds:
            raise IcommandException('Unsupported icommand: "%s"'%(icmd,))
        
        if arg_list == None:
            arg_list = []

        #! logging.debug('icmd env=%s'%(self.env,))
        args = [icmd] + arg_list
        #!logging.debug('icmd call=%s'%(' '.join(args),))
        logging.debug('icmd call=%s'%(args,))
        return subprocess.check_output(args, env=self.env)


    # iput returns error if attempt to write to existing file
    def iput(self, flags, local_fname_list, irod_fname):
        return self.run_icmd('iput',arg_list=[flags]+local_fname_list+[irod_fname])

    def iget(self,irod_fname, local_fname):
        return self.run_icmd('iget',arg_list=[irod_fname, local_fname])

    def imkdir(self, path):
        return self.run_icmd('imkdir',  arg_list=['-p', path])

    def irsync(self, *args):
        return self.run_icmd('irsync',list(args))

    def ils(self, *args):
        return self.run_icmd('ils',list(args))

