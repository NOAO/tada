import yaml
import logging
import time
import traceback
import sys
import os.path
import re


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
        lut[(d['site'],
             d['telescope'],
             d['instrument']
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

##############################################################################
def read_errcode_list_yaml(yamlfile):
    if not os.path.exists(yamlfile):
        return list()

    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise

    # INPUT: [dict(name, regexp),...]
    # OUPUT: [(ERRCODE, MatchREGEXP, ShortDesc), ...]
    ll = [(d['name'], re.compile(d['regexp']), None) for d in res]
    return ll

def read_errcode_yaml():
    return read_errcode_list_yaml('/etc/tada/errcode_table.yaml')

##############################################################################
def read_name_set_yaml(yamlfile):
    if not os.path.exists(yamlfile):
        return set()

    try:
        res = read_yaml(yamlfile)
    except Exception as err:
        logging.error('Could not read YAML file {}; {}'
                      .format(yamlfile, err))
        raise

    # INPUT: [dict(name, comment),...]
    # OUPUT: set([name, ...])
    return set([d['name'] for d in res])

def read_rawreq_yaml():
    return read_name_set_yaml('/etc/tada/raw_required_table.yaml')
def read_fnreq_yaml():
    return read_name_set_yaml('/etc/tada/filename_required_table.yaml')
def read_ingestreq_yaml():
    return read_name_set_yaml('/etc/tada/ingest_required_table.yaml')
def read_ingestrec_yaml():
    return read_name_set_yaml('/etc/tada/ingest_recommended_table.yaml')
def read_supportreq_yaml():
    return read_name_set_yaml('/etc/tada/support_required_table.yaml')
def read_float_yaml():
    return read_name_set_yaml('/etc/tada/float_table.yaml')


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


# WARNING: tricky stuff lurks inside here
def dynamic_load(pyfilename):
    if not os.path.exists(pyfilename):
        return dict()

    myfuncs = dict()
    try:
        with open(pyfilename) as pf:
            codestr = pf.read()
            exec(codestr,globals(), myfuncs)
    except Exception as err:
        logging.error('Error executing python code in ({});{}'
                      .format(pyfilename, err))
    return myfuncs

def dynamic_load_hdr_funcs():
    """\
RETURNS: localdict,  such that:
  localdict[funcname]     => func
     func.inkws  => [kw1, kw2, ...]
     func.outkws => [...]
  localdict[in_keywords]  => [kw, ...] (union of inkws  for ALL funcs)
  localdict[out_keywords] => [kw, ...] (union of outkws for ALL funcs)
  func(orig, **kwargs) => newhdrdict
"""
    return dynamic_load('/etc/tada/hdr_funcs.py')
