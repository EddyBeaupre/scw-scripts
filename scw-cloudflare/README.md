# scw-cloudflare

This script will update or create A or AAAA records on cloudflare using the
server's metadata. Update will only be send if the A or AAAA records differ
from the IPv4 or IPv6 address reported by the server's metadata or does not
exist.

## Configuration

Make sure you have the `cloudflare` python module. You can install it with:

```
pip install cloudflare
```

The configuration file must be copied to the /etc directory and with the
same name as this script, but with the extension change to .conf (IE, if
your script is renamed to `fixmydns`, the configuration file will be
`/etc/fixmydns.conf`)

The configuration file consist of the DEFAULT section, and various server
definition sections.

```
[DEFAULT]
scwMetaData = /usr/local/bin/scw-metadata-json
apitoken="XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

scwMetaData - Optional
              specify the location of the scw-metadata-json script.
apitoken    - Mendatory
              API key, must have `Zone.DNS` permission on the zones
              you want to update.

```
[server1.domain.com]
ipv4 = True
ipv6 = True
proxied = Keep
```

All other sections should be name exactly like the A or AAAA record you want
to update. `ipv4` must be set to true to update the A record and `ipv6` to
update the AAAA record. `proxied` can be True (proxy the record), false (do
not proxy the record) or anything else to keep the current value.

## Logging

Logging is done with syslog entries.

## Startup script

Create a one-shot systemd unit named `/etc/systemd/system/scw-cloudflare.service`

```
[Unit]
Description=Update cloudflare entries at startup

[Service]
ExecStart=/usr/local/bin/scw-cloudflare
Type=oneshot
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Then run the following commands to activate the one-shot script at startup:

```
sudo systemctl daemon-reload
sudo systemctl enable scw-cloudflare.service
```
