CREATE TABLE audit(
	md5sum,         -- of FITS file
	obsday date,	-- observation day
	telescope not null, 
	instrument not null,
	srcpath not null,	-- full path of FITS file
	recorded timestamp,	-- when srcpath was recorded
	submitted timestamp,	-- when submitted to archive
	success,		-- NULL until ingest attempted. Then True iff
				-- archive reported success on ingest
	archerr,	-- Error message (if applicable) of Archive Ingest
	archfile,	-- basename of FITS file in Archive
	PRIMARY KEY (telescope, instrument, srcpath)
	);
