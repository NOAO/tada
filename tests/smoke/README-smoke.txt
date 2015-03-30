This directory contains "smoke tests".

Smoke tests are intended to be easy to create tests that run
quickly. Run time more than a few minutes is NOT considered quick.
They are expected to be used just before checkin and after
checkout to answer the question: "Does it seem to working ok?".

They are definitely NOT either "regression" or "unit" tests.
They are not regression tests because they don't try to cover a lot of
cases (which would cause them to take too long to run). They are not
unit tests because they are done at the level of PROGRAM output, not
internal functions.

Because smoke tests are easy to create and run, they are appropriate
for prototype code.  They help developers be more courageous by
requiring less inspection to determine if specific changes broke
anything.

For software further along in Technical Readiness Level, regression
and unit tests should also be used.

----------------

Good smoke testing of TADA is difficult.  The results of submitting a
file to TADA in an operational environment include many aspects:
- handling of 3 kinds of files
  + non-FITS, compliant FITS, non-compliant FITS
- Final resting places of all 3 kinds of files and of files that don't
  make it through the whole data-flow due to system failure
  + local files/directories on various machines, iRODS, portal
- trapping and reporting of failure conditions via:
  + TADA log, email, syslog
- failure modes on any of the machines in the TADA data-flow
  + lost connections, full disk/RAM, services killed


Add to this: timing issues, implicit requirements, networking delays,
and opaque services.   And, we want a smoke test that runs "quickly"
so that its reasonable to run after every significant code or system
change.

The current smoke test does NOT meet all of our goals for a smoke
test.  My best hope is that the current tests are good enough, and
that it additional smoke tests can be added by someone not intimately
familiar with the TADA system.  Tests in generaly should be viewed as
organic; they should grow to remain relevant. 
