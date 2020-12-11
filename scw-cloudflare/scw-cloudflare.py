#!/bin/env python3

from argparse import ArgumentParser
from posix import EX_OK, EX_SOFTWARE, EX_USAGE, EX_UNAVAILABLE
from CloudFlare import CloudFlare, exceptions as CFExceptions
from configparser import ConfigParser
from ipaddress import ip_address as IPAddress
from logging.handlers import SysLogHandler
from logging import Formatter, getLogger as GetLogger, debug as LogDebug, info as LogInfo, warning as LogWarning, error as LogError, critical as LogCritical, exception as LogException
from os.path import splitext as SplitExt, basename as BaseName
from os import getpid as GetPid, environ as OSEnviron, popen
from sys import exit as SysExit
from syslog import syslog as SysLog
from json import loads as JLoads
from subprocess import check_output


scriptConfig = None


class ScriptConfig:
    Name, Extension = SplitExt(BaseName(__file__))
    ConfigFile = "/etc/" + Name + ".conf"
    Version = "0.10.0"
    Config = None
    Host = None

    def __init__(self):
        self.Config = ConfigParser()
        self.Config.sections()
        self.Config.read(self.ConfigFile)
        if self.HasOption('DEFAULT', 'scwMetaData'):
            self.Host = JLoads(check_output([self.Config['DEFAULT']['scwMetaData']]))
        else:
            self.Host = JLoads(check_output(["/usr/local/bin/scw-metadata-json"]))

    def GetToken(self):
        try:
            return self.Config['DEFAULT']['apitoken']
        except:
            return None

    def GetIP(self):
        try:
            return self.Host['public_ip']['address'], self.Host['ipv6']['address']
        except:
            return None, None

    def HasOption(self, section, item):
        try:
            return self.Config.has_option(section, item)
        except:
            return None

    def GetItems(self):
        try:
            return self.Config.items()
        except:
            return None

    def GetValue(self, section, item):
        try:
            return self.Config[section].get(item)
        except:
            return None

    def GetInt(self, section, item):
        try:
            return self.Config[section].getint(item)
        except:
            return 0

    def GetFloat(self, section, item):
        try:
            return self.Config[section].getfloat(item)
        except:
            return 0

    def GetBoolean(self, section, item):
        try:
            return self.Config[section].getboolean(item)
        except:
            return False

    def GetBooleanNone(self, section, item):
        try:
            return self.Config[section].getboolean(item)
        except:
            return None


def updateRecord(dnsRecord, ipAddress, proxied, cfToken):
    isUpdate = False
    isPresent = False
    try:
        hostName, zoneName = '.'.join(dnsRecord.split('.')[:2]), '.'.join(dnsRecord.split('.')[-2:])
        ipInfo = IPAddress(ipAddress)
        cf = CloudFlare(token=cfToken)
        recordType = "A"
        recordContent = ipInfo.compressed
        if ipInfo.version == 6:
            recordType = "AAAA"
        LogDebug("Zone Name: {}, DNS Record: {}, IP Address: {}({})".format(zoneName, dnsRecord, recordContent, recordType))
        zones = cf.zones.get(params={'name': zoneName})
        for zone in zones:
            LogDebug("Searching zone {}".format(zone['name']))
            dnsRecords = cf.zones.dns_records.get(zone['id'], params={'name': dnsRecord, 'match': 'all', 'type': recordType})
            for dnsRecord in dnsRecords:
                LogDebug("Examining record {}".format(dnsRecord['name']))
                if dnsRecord['type'] == recordType:
                    LogDebug("Record type match")
                    isPresent = True
                    if dnsRecord['content'] != recordContent:
                        LogDebug("Record need updating")
                        if proxied != None:
                            dnsRecord['proxied'] = proxied
                        newRecord = {'name': dnsRecord['name'], 'type': dnsRecord['type'], 'content': recordContent, 'proxied': dnsRecord['proxied']}
                        cf.zones.dns_records.put(zone['id'], dnsRecord['id'], data=newRecord)
                        LogInfo("Zone Name: {}, DNS Record {}: {}({}) - Updated".format(zone['name'],
                                                                                        newRecord['name'], newRecord['content'], newRecord['type']))
                        isUpdate = True
                    else:
                        LogInfo("Zone Name: {}, DNS Record {}: {}({}) - Up to date".format(zone['name'],
                                                                                           dnsRecord['name'], dnsRecord['content'], dnsRecord['type']))
                else:
                    LogInfo("Zone Name: {}, DNS Record {}: {}({}) - Type does not match ({})".format(
                        zone['name'], dnsRecord['name'], dnsRecord['content'], dnsRecord['type'], recordType))
        if not isPresent:
            LogDebug("Record not found, adding record")
            for zone in zones:
                LogDebug("Searching zone {}".format(zone['name']))
                if zone['name'] == zoneName:
                    if proxied == None:
                        proxied = False
                    cf.zones.dns_records.post(zone['id'], data={'name': dnsRecord, 'type': recordType, 'content': recordContent, 'proxied': proxied})
                    LogInfo("Zone Name: {}, DNS Record {}: {}({}) - Added".format(zone['name'], dnsRecord, recordContent, recordType))
                    isUpdate = True
    except CFExceptions as e:
        LogError("Cloudflare exception: {}".format(e))
    except Exception as e:
        LogError("Error while updating record: {}".format(e))
    finally:
        return isUpdate


def main(ArgParser):
    scriptConfig = ScriptConfig()
    try:
        handler = SysLogHandler('/dev/log')
        formatter = Formatter(scriptConfig.Name + '[' + str(GetPid()) + ']: %(message)s')
        handler.setFormatter(formatter)
        root = GetLogger()
        root.setLevel(OSEnviron.get("LOGLEVEL", "INFO"))
        root.addHandler(handler)
    except Exception as e:
        SysLog.syslog('Error while initializing logger: {}'.format(e))
        return EX_UNAVAILABLE

    try:
        ArgParser.add_argument("-v", '--version', action='version', version=scriptConfig.Name + " version " + scriptConfig.Version)
        ArgParser.add_argument("-d", "--debug", action='store_true', default=False, dest="debug", help="Log debug information to syslog")
        options = ArgParser.parse_args()

        if options.debug:
            root = GetLogger()
            root.setLevel(OSEnviron.get("LOGLEVEL", "DEBUG"))
    except Exception as e:
        LogError('Error while parsing arguments: {}'.format(e))
        return EX_USAGE

    try:
        LogInfo("Version " + scriptConfig.Version)

        ipv4, ipv6 = scriptConfig.GetIP()
        if scriptConfig.HasOption('DEFAULT', 'apitoken'):
            for item, data in scriptConfig.GetItems():
                if item != 'DEFAULT':
                    if scriptConfig.GetBoolean(item, 'ipv4'):
                        updateRecord(item, ipv4, scriptConfig.GetBooleanNone(item, 'proxied'), scriptConfig.GetToken())
                    if scriptConfig.GetBoolean(item, 'ipv6'):
                        updateRecord(item, ipv6, scriptConfig.GetBooleanNone(item, 'proxied'), scriptConfig.GetToken())
        else:
            LogError("Please set 'apitoken' in {}".format(scriptConfig.ConfigFile))
    except Exception as e:
        LogError('Error while updating record: {}'.format(e))
        return EX_SOFTWARE

    return EX_OK


if __name__ == '__main__':
    try:
        SysExit(main(ArgumentParser(description="Update dns entries on cloudflare.")))
    except Exception as e:
        LogError(e)
        pass
