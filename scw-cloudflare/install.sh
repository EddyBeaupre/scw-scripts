#!/bin/bash
cp scw-cloudflare.py /usr/local/bin/scw-cloudflare
cp scw-cloudflare.service /etc/systemd/system/scw-cloudflare.service
cp scw-cloudflare.crond /etc/cron.d/scw-cloudflare
if [ ! -f /etc/scw-cloudflare.conf ]; then
  cp scw-cloudflare.conf.example /etc/scw-cloudflare.conf
fi
systemctl daemon-reload
systemctl enable scw-cloudflare.service
echo "Install done, Please edit /etc/scw-cloudflare.conf before starting the service."
