CREATE TABLE audit(
	telescope not null,
	instrument not null,
	srcpath not null,
	recorded,
	submitted,
	success,
	archerr,
	archfile,
	PRIMARY KEY (telescope, instrument, srcpath)
	);
