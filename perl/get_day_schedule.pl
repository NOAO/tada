#!/usr/bin/perl -w
# PURPOSE:
#    Output schedule information from SOAP based web-service into XML.
#
# USAGE:
#   get_day_schedule.pl [--date=<yyyy-mm-dd>] [--telescope=<tele> ]...
#
# EXAMPLES:
#    get_day_schedule.pl --help 
#    get_day_schedule.pl --telescope=kp4m --telescope=ct4m
#    get_day_schedule.pl --date=2015-01-05 --telescope=kp4m  >schedule.xml 
#
#    # for today; internal list of all known (at time of writing) telescopes
#    get_day_schedule.pl > schedule.xml   
#
#    get_day_schedule.pl  --comment "Testing 1 2 3" --telescope=kp4m 
#    
# AUTHORS: S.Pothier
#
# NOTES:
#    How does it work?  What design ideas did you use? What design ideas
#    did you discard?  Why? 
#

#
# Robbed from Rob, see:
# GETSCHEDULE -- script to retrieve NOAO proposal information and build
# local keyword=value text database to allow iSTB to update each incoming
# header with proposal ID, proprietary period and other pertinent info.
# R. Seaman, 2004-07-09, based on services and code by D. Gasson

use strict ;

use Getopt::Long;
use SOAP::Lite;
use XML::XPath;
use XML::XPath::XMLParser;
use File::Basename;

my (@telescopes, $date);
my ($prog, $args, $comment, $help, $usage, $version, $today);

$version="0.5";

$prog=basename($0);
$args = join(" ",@ARGV);
&GetOptions(
    "date=s"	=> \$date,
    "telescope=s"	=> \@telescopes,
    "comment=s"	=> \$comment,
    "help"	=> \$help
    );

$usage="
VERSION: $version


USAGE: $prog [options]
Options:
  --date        Get schedule for (yyyy-mm-dd) date. Default: today
  --telescope   Get schedule for named telescope. Can be used multiple times.
                Default: all known telescopes
  --comment	Comment to put in XML file header.
  --help	Display this information
";
if ($help) {
    print STDERR $usage;
    exit;
};

$today = `date +"%Y-%m-%d"`;
chop $today;

# defaults
if (scalar(@telescopes) == 0) {
    @telescopes = qw(ct09m ct13m ct15m ct1m 
                     gem_n gem_s 
		     het 
                     keckI keckII 
                     kp09m kp13m kp21m kp4m kpcf 
                     magI magII 
                     mmt soar wiyn);
}
$date ||= $today;
$comment ||= "NA";

my $response = SOAP::Lite
    -> uri ('http://www.noao.edu/Andes/ScheduleSearch')
    -> proxy ('http://www.noao.edu/cgi-bin/webservices/andes/dispatch.pl');

my $propXml;


 
print "<!--
TITLE:   Proposal Schedule results from web-service
VERSION: $version
COMMENT: $comment
Run_DATE:      $today
Schedule_DATE: $date
-->

<results>
";

foreach my $tel (@telescopes) {
    # $date :: yyyy-mm-dd
    #! print STDERR "# CALL: getProposalScheduleOn($tel, $date)\n";
    my $result = $response->getProposalsScheduledOn ($tel, $date);
    unless ($result->fault) {
	$propXml = $result->result ();
    } else {
	print join ', ', $result->faultcode, $result->faultstring;
    }
    print "$propXml\n";

}

print "\n</results>\n";
