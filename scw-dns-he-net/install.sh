#!/bin/bash
cp scw-dns-he-net.py /usr/local/bin/scw-dns-he-net
cp scw-dns-he-net.service /etc/systemd/system/scw-dns-he-net.service
cp scw-dns-he-net.crond /etc/cron.d/scw-dns-he-net
if [ ! -f /etc/scw-dns-he-net.conf ]; then
  cp scw-dns-he-net.conf.example /etc/scw-dns-he-net.conf
fi
systemctl daemon-reload
systemctl enable scw-dns-he-net.service
echo "Install done, Please edit /etc/scw-dns-he-net.conf before starting the service."
