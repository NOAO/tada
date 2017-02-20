import yaml
import logging
import time
import traceback
import sys
import os.path


def read_yaml(yamlfile):
    with open(yamlfile) as f:
        res = yaml.safe_load(f)
    return res

# Add "schema" validation for each kind of yaml read!!!
def read_hiera_yaml():
    yamlfile = '/etc/tada/hiera.yaml'
    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise
    return res

def read_tada_yaml():
    yamlfile = '/etc/tada/tada.conf'
    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise
    return res

def read_sti_yaml():
    yamlfile = '/etc/tada/prefix_table.yaml'
    if not os.path.exists(yamlfile):
        return dict()

    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise

    # INPUT: [dict(instrument__name, prefix, site__name, telescope__name),...]
    # OUPUT: dict[(site, telescope,instrument)] => prefix
    lut = dict()
    for d in res:
        lut[(d['site__name'],
             d['telescope__name'],
             d['instrument__name']
        )] = d['prefix']
    
    return lut

def read_name_code_yaml(yamlfile):
    if not os.path.exists(yamlfile):
        return dict()

    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise

    # INPUT: [dict(name, code),...]
    # OUPUT: dict[name] => code
    lut = dict()
    for d in res:
        lut[d['name']] = d['code']
    return lut

def read_obstype_yaml():
    return read_name_code_yaml('/etc/tada/obstype_table.yaml')

def read_proctype_yaml():
    return read_name_code_yaml('/etc/tada/proctype_table.yaml')

def read_prodtype_yaml():
    return read_name_code_yaml('/etc/tada/prodtype_table.yaml')

def tic():
    tic.start = time.perf_counter()

def toc():
    elapsed_seconds = time.perf_counter() - tic.start
    return elapsed_seconds # fractional


def log_traceback():
    """Log a traceback with sufficient detail to point to source of error.
NOTE: The traceback (stack) itself is logged to INFO, not ERROR. This is to
allow tests to use ERROR and WARNING logging to insure correct behavior. Stacks
have line numbers so would cause unsability in GOLD files.
"""
    etype, evalue, tb = sys.exc_info()

    logging.error(traceback.format_exception_only(etype, evalue)[0]+'!')

    #!ll = traceback.format_exception_only(etype, evalue)
    #!ll = traceback.format_exception(etype, evalue, tb)
    #!logging.info(';'.join([s.replace('\n','') for s in ll]))
    logging.debug(traceback.format_exc()) # multi-line human readable

    
def trace_if(trace):    
    if trace:
        traceback.print_exc()
    

def dict_str(dict):
    """Return string that formats content of dictionary suitable for log"""
    return '[' + ', '.join(['{}={}' for k,v in dict.items()]) + ']'


