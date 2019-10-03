# scw-dns-he-net

This script will update A or AAAA records on dns.he.net using the server's
metadata.

# Configuration

The configuration file must be copied to the /etc directory and with the
same name as this script, but with the extension change to .conf (IE, if
your script is renamed to 'fixmydns', the configuration file will be
'/etc/fixmydns.conf')

The configuration file consist of the DEFAULT section, and various server
definition sections.

```
[DEFAULT]
scwMetaData = /usr/local/bin/scw-metadata-json
nameServers = ns1.he.net ns2.he.net ns3.he.net ns4.he.net ns5.he.net
```

The default section and any of it's parameters are optionnals. If is used to
override defaults parameters of the scripts. `scwMetaData` let you specify a
different executable that will be used to retreive the server's metadata and
`nameServers` let you specify other nameservers than he.net's to validate if
your ip has change from the DNS records.

```
[server1.domain.com]
Key = <ddns update key>
IPv4 = True
IPv6 = True
```

All other sections should be name exactly like the A or AAAA record you want
to update. 'Key' must be set to your ddns update key, 'IPv4' must be set to
true to update the A record and 'IPv6' to update the AAAA record.
