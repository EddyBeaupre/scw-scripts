#!/usr/bin/env python3

import json
import os
import dns.resolver
import requests
import configparser
import syslog
import shutil

scriptName, scriptExtension = os.path.splitext(os.path.basename(__file__))
configFile = "/etc/" + scriptName + ".conf"
syslog.syslog(syslog.LOG_INFO, scriptName + " initializing")

syslog.syslog(syslog.LOG_INFO, 'Reading configuration file ' + configFile)
config = configparser.ConfigParser()
config.sections()
config.read(configFile)

if not config.has_option('DEFAULT', 'scwMetaData'):
  config['DEFAULT']['scwMetaData']=shutil.which('scw-metadata-json')
  syslog.syslog(syslog.LOG_INFO, 'Using default ' + config['DEFAULT']['scwMetaData'] + " for server's metadata")
else:
  syslog.syslog(syslog.LOG_INFO, 'Using custom ' + config['DEFAULT']['scwMetaData'] + " for server's metadata")
  
if not config.has_option('DEFAULT', 'nameServers'):
  syslog.syslog(syslog.LOG_INFO, 'Using default nameservers for valdation')
  config['DEFAULT']['nameServers']="ns1.he.net ns2.he.net ns3.he.net ns4.he.net ns5.he.net"
else:
  syslog.syslog(syslog.LOG_INFO, 'Using nameservers ' + config['DEFAULT']['nameServers'] + " for validation")

syslog.syslog(syslog.LOG_INFO, "Reading SCW MetaData")
scwMetaData = json.loads(os.popen(config['DEFAULT']['scwMetaData']).read())

def getNameServers():
  nameServer = []
  syslog.syslog(syslog.LOG_INFO, 'Parsing nameservers list')
  for ns in config['DEFAULT']['nameServers'].split():
    answers = dns.resolver.query(ns, 'A')
    for rdata in answers:
      syslog.syslog(syslog.LOG_INFO, 'NameServer ' + ns + ' IPv4 address: ' + rdata.address)
      nameServer.append(rdata.address)
    answers = dns.resolver.query(ns, 'AAAA')
    for rdata in answers:
      syslog.syslog(syslog.LOG_INFO, 'NameServer ' + ns + ' IPv6 address: ' + rdata.address)
      nameServer.append(rdata.address)
  return nameServer;

def dnsResolver( dnsServer, dnsName, dnsType ):
  """
  Resolve DNS entries
  """
  dnsAnswer = []
  try:
    syslog.syslog(syslog.LOG_INFO, 'Initializing resolver')
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = dnsServer
    answers = resolver.query(dnsName, dnsType)
    for rdata in answers:
      syslog.syslog(syslog.LOG_INFO, dnsName + ' (' + dnsType + ") resolve to " + rdata.address)
      dnsAnswer.append(rdata.address)
    return dnsAnswer
  except:
    syslog.syslog(syslog.LOG_INFO, dnsName + ' (' + dnsType + ") did not resolve")
    return dnsAnswer

def updateIP(hostname, password, address):
  """
  Update a dynamic record
  """
  syslog.syslog(syslog.LOG_INFO, "Updading " + hostname + " address to " + address)
  data = {'hostname':hostname, 'password':password, 'myip':address}
  result = requests.post(url = "https://dyn.dns.he.net/nic/update", data = data)
  syslog.syslog(syslog.LOG_INFO, "Updading " + hostname + " result: " + result.text)
  return result
  
def str2bool(v):
  return v.lower() in ("yes", "ye", "y", "true", "tru", "tr", "t", "oui", "ou", "o", "1")
  
def needUpdate(dnsServer, ipAddress, dnsName, dnsType):
  for address in dnsResolver(dnsServer, dnsName, dnsType):
    if ipAddress == address:
      syslog.syslog(syslog.LOG_INFO, dnsName + " (" + dnsType + ") is up to date")
      return False
  syslog.syslog(syslog.LOG_INFO, dnsName + " (" + dnsType + ") need update")
  return True
  
dnsServer = getNameServers()

for item in config.items():
  if item[0] != 'DEFAULT':
    if str2bool(config[item[0]]['IPv4']):
      if needUpdate(dnsServer, scwMetaData['public_ip']['address'], item[0], "A"):
        updateIP(item[0], config[item[0]]['Key'], scwMetaData['public_ip']['address'])
    if str2bool(config[item[0]]['IPv6']):
      if needUpdate(dnsServer, scwMetaData['ipv6']['address'], item[0], "AAAA"):
        updateIP(item[0], config[item[0]]['Key'], scwMetaData['ipv6']['address'])
