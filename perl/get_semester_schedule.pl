#!/usr/bin/perl
#
# GETSEMESTERXML - Dumps a semester of proposals to XML
#
# Usage: getSemesterXML [test|prod] --sem=SEMESTER
#
#    --sem=SEMESTER
#          SEMESTER is in the format YYYYA or YYYYB and specifies
#          the semester for which to dump the proposal information.
#    --dbname=NAME
#          NAME is the name of the metadata database to use.
#    --dbhost=HOST
#          HOST is the name of the host machine for the metadata db.
#          IF this is defined, then the CONFIG_FILE values will be ignored
#          (This option is useful for unit testing)
#    --dbport=PORT
#          PORT is the DBI port of the database
#    --dbuser=USER
#          USER is the name of the db user
#    --dbpassword=PASSWORD
#          PASSWORD is the password for the db user
#
# Revision History:
#     2008-08-07 - dscott@noao.edu
#         Initial release.
#
#     2010-12-10 - erikt@noao.edu
#         Modified SOAP call (line 125) to use new SOAP method.
#     2010-12-20 - bthomas@noao.edu
#         Modified to allow passing db parameters on commandline instead of config file
#
#     2011-12-14 - erikt@noao.edu
#      Forced encoding to iso-8859-1.  Removed username and passwords.
#
#     2011-11-15 - dscott@noao.edu
#         Removed all old references to PlanB...Archive is well beyond PlanB
#         and there is no reason to support it anymore.
#         Removed references to the CONFIG_DIR which stores the archive
#         deployment configuration files, all database parameters now must
#         be specified on the command line.
#         Removed duplicated, commented out, check that the PI's e-mail
#         address field contains a value.
#         Added a suggested check that the Co-I's e-mail address field is
#         checked to contain a value, if not, issues a message that the Co-I
#         will be ignored and removed from the XML dump.

use strict;

use Encode;
use Getopt::Long;
use SOAP::Lite;
use XML::LibXML;

my ($sem, $db_host, $db_name, $db_port, $db_user, $db_pass);
GetOptions ( 'sem=s' => \$sem, 'dbhost=s' => \$db_host,
              'dbname=s' => \$db_name, 'dbport=n' => \$db_port,
              'dbuser=s' => \$db_user, 'dbpassword=s' => \$db_pass,
            );

$sem ||= '2007A';
$db_user ||= 'none';
$db_name ||= 'metadata';
$db_port ||= 5432;
$db_pass ||= 'none';

if ("$db_user" eq "" or "$db_pass" eq "") {
   print "Must supply at least the username and password used to connect to $db_name!\n";
   exit 2;
}


sub valid_period ($) {
   my $proposal = $_[0];
   return defined ($proposal->{'parameter'}[0]->{'content'});
}

sub valid_email ($) {
   my $proposal = $_[0];
   return defined ($proposal->{'investigator'}[0]->{'email'}[0]);
}

sub valid_affil ($) {
   my $proposal = $_[0];
   return defined ($proposal->{'investigator'}[0]->{'affiliation'}[0]);
}

my $response = SOAP::Lite
   -> uri('http://www.noao.edu/Andes/ScheduleSearch')
   -> proxy('http://www.noao.edu/cgi-bin/webservices/andes/dispatch.pl');

my %isWarned;
my @userWarnings;
#my $result = $response->getProposalContactInformationWithCoIFor($sem);
my $result = $response->getProposalContactInformationFor($sem);
unless ($result->fault)
{
    print($result->result ());

    # Does not work because the service produces XML with prefix but
    # no defintion.
    #! my $dom = XML::LibXML->load_xml(string => $result->result ());
    #! print $dom->toString();
} else {
    warn $result->fault."\n";
}


foreach my $warn (sort { lc($a) cmp lc($b) } @userWarnings) { warn $warn; }
