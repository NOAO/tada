'Accumalate FITS header changes to apply later.'
# UNDER CONSTRUCTION!!!

# INPUTS:
#  original header
#  modified header (updates aggregated)
#  definitions in YAML (python for hdr funcs)
#  procedure YAML (python)
#
# OUTPUTS:
#  change applied to new FITS header
#  list of fields to delete
#  (automatic HISTORY entries in FITS header)
#
# Validate all YAML on load.
# How would this look if done in Scheme?
# Intended for use by TADA, DART


import logging
import datetime
import pkg_resources

class HeaderChange():
    """Accumulate changes that will eventually be made to a FITS header.
Changes may include:
  - change field values
  - delete fields
  - addition to HISTORY
  - addition to COMMENT

orig:: the original FITS header as dict
"""
    def __init__(self, origdict, **kwargs):
        self.orig = origdict.copy()
        self.new = origdict.copy() 
        self.removekeys = list()
        self.history = list()
        self.comment = list()

    def change(self, key, newvalue):
        self.new[key] = newvalue
        
    def apply(self, fitsheader):
        fitsheader['HISTORY'] = ('TADA modified header on: {}'
                                 .format(datetime.datetime.now().isoformat()))
        # pylint: disable=no-member
        vers = pkg_resources.get_distribution('tada').version
        fitsheader['HISTORY'] = 'TADA version: {}'.format(vers)

        # Change values and record change in history
        for k,val in self.new.items():
            hist = ('Changed key ({}) from value ({}) to ({}).'
                    .format(k,
                            fitsheader.get(k,'<none>'),
                            val))
            fitsheader[k] = val
            fitsheader['HISTORY'] = hist

        # Delete keys and record change in history
        for kw in self.removekeys:
            hist = ('Removed key ({}) with value ({}).'
                    .format(kw, fitsheader[kw]))
            fitsheader['HISTORY'] = hist
            del fitsheader[kw]

        # Add additional HISTORY and COMMENT cards
        for s in self.history:
            fitsheader['HISTORY'] = s
        for s in self.comment:
            fitsheader['COMMENT'] = s
            
        return fitsheader
