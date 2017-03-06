from . import utils as tut


hiera = tut.read_hiera_yaml()
tada = tut.read_tada_yaml()

dq_host = hiera['dq_host']
dq_port = hiera['dq_port']
dq_loglevel = hiera['dq_loglevel']
dq_unblock_timeout = hiera.get('dq_unblock_timeout',0)
arch_host = hiera['arch_host']
arch_port = hiera['arch_port']
arch_timeout = hiera.get('arch_timeout', 10)
arch_irods_host = hiera['arch_irods_host']
arch_irods_port = hiera['arch_irods_port']
arch_irods_resource = hiera['arch_irods_resource']
archive_irods331 = hiera['archive_irods331']
valley_host = hiera['valley_host']
mars_host = hiera['mars_host']
mars_port = hiera['mars_port']
do_audit = hiera.get('do_audit', True)

maximum_queue_size  = tada['maximum_queue_size']
redis_port = tada['redis_port'] # 6379
pre_action = tada.get('pre_action',None)


#dict([(v,getattr(settings,v)) for v in dir(settings) if not v.startswith("_")])

# Load FITS filename prefix table (ultimately creating using MARS)
stiLUT = tut.read_sti_yaml()
obsLUT = tut.read_obstype_yaml()
procLUT = tut.read_proctype_yaml()
prodLUT = tut.read_prodtype_yaml()

RAW_REQUIRED_FIELDS = tut.read_rawreq_yaml()
FILENAME_REQUIRED_FIELDS = tut.read_fnreq_yaml()
INGEST_REQUIRED_FIELDS = tut.read_ingestreq_yaml()
INGEST_RECOMMENDED_FIELDS = tut.read_ingestrec_yaml()
SUPPORT_FIELDS = tut.read_supportreq_yaml()
FLOAT_FIELDS = tut.read_float_yaml()
ERRMAP = tut.read_errcode_yaml()

# see ../getconfig/from_mars.py for detail of dict format
# also utils.py:dynamic_load_hdr_funcs()
HDR_FUNCS = tut.dynamic_load_hdr_funcs() # dict[funcname]=func
