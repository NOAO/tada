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
