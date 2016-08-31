import yaml
import logging
import time

def read_hiera_yaml():
    hiera_filename = '/etc/tada/hiera.yaml'
    res = None
    with open(hiera_filename) as f:
        res = yaml.safe_load(f)
    return res

def tic():
    tic.start = time.perf_counter()

def toc():
    elapsed_seconds = time.perf_counter() - tic.start
    return elapsed_seconds # fractional
