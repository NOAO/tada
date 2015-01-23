

* From:https://en.opensuse.org/SDB:CUPS_in_a_Nutshell

Client-only configuration:

If browsing is generally undesired, there is no reason for running a
cupsd on the client. In this case, a client-only configuration should
be used. Either set it up manually as described below or use
YaST. Since openSUSE 11.1 use in YaST the "Print via Network" dialog,
see YaST Printer.

1. Stop and deactivate cupsd (using the YaST Runlevel Editor or insserv).
2. In /etc/cups/client.conf, insert an entry in the form "ServerName
   IP.of.the.server".

Such an entry in /etc/cups/client.conf should not exist together with
a running local cupsd. As only one entry is possible, the preferred
server should be entered. To access a different server, the server
must be specified explicitly (option "-h") when using the command-line
tools, or the environment variable CUPS_SERVER must be set
accordingly. Some applications ignore the "ServerName" entry. In this
case, it may be useful to set CUPS_SERVER, or the server can be
specified explicitly in the application (e.g., with the option "-h" in
the print command).

