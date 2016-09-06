from . import utils as tut
from . import audit


hiera = tut.read_hiera_yaml()

dq_host = hiera.get('dq_host')
dq_port = hiera.get('dq_port')
dq_loglevel = hiera.get('dq_loglevel')
dq_unblock_timeout = hiera.get('dq_unblock_timeout')
arch_host = hiera.get('arch_host')
arch_port = hiera.get('arch_port')
arch_irods_host = hiera.get('arch_irods_host')
arch_irods_port = hiera.get('arch_irods_port')
arch_irods_resource = hiera.get('arch_irods_resource')
archive_irods331 = hiera.get('archive_irods331')
valley_host = hiera.get('valley_host')
mars_host = hiera.get('mars_host')
mars_port = hiera.get('mars_port')

max_queue_size  = hiera.get('maximum_queue_size')

auditor = audit.Auditor()
