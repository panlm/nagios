#!/usr/bin/env python
# depends py-zabbix, using 'pip install py-zabbix' to install it.
# snmpwalk -v3 -l authPriv -u nutanix -A '12345678' -a SHA -x AES -X '12345678' 10.132.68.23 .system
# session = netsnmp.Session(DestHost='10.132.68.23', Version=3, SecLevel='authPriv', AuthProto='SHA', AuthPass='12345678', PrivProto='AES', PrivPass='12345678', SecName='nutanix')
# version 1

import re
import sys
import os
import time
import netsnmp
import argparse
from os import stat
from pyzabbix import ZabbixAPI, ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', action="store", dest='snmpversion', default=2, type=int)
parser.add_argument('-H', '--hostname', action="store", dest='hostname', default='localhost')
parser.add_argument('-C', '--community', action="store", dest='community', default='public')
parser.add_argument('-p', '--perfdata', action="store_true", dest='perfdata', default=False)
parser.add_argument('-z', '--zabbix', action="store_true", dest='zabbix', default=False)
parser.add_argument('-D', '--debug', action="store_true", dest='isdebug', default=False)
# for snmp v3
parser.add_argument('-u', '--username', action="store", dest='username', default='nutanix')
parser.add_argument('-l', action="store", dest='seclevel', default='authPriv')
parser.add_argument('-a', action="store", dest='authproto', default='SHA')
parser.add_argument('-A', action="store", dest='authpass', default='12345678')
parser.add_argument('-x', action="store", dest='privproto', default='AES')
parser.add_argument('-X', action="store", dest='privpass', default='12345678')
# for zabbix
parser.add_argument('--zabbix_server', action="store", dest='zabbix_server', default='zabbix')
parser.add_argument('--zabbix_user', action="store", dest='zabbix_user', default='Admin')
parser.add_argument('--zabbix_pass', action="store", dest='zabbix_pass', default='zabbix')
#    zabbix_server = '10.132.71.160'
#    zabbix_user = 'Admin'
#    zabbix_password = 'zabbix'

param = parser.parse_args()
if param.isdebug:
    print param.zabbix_server,param.zabbix_user,param.zabbix_pass

if param.snmpversion == 3:
    if param.username == '' or param.authpass == '' or param.privpass == '':
        print "-u, -A and -X are needed when snmpversion is 3\n"
        sys.exit(1)

session = netsnmp.Session(DestHost=param.hostname, Version=param.snmpversion, SecLevel=param.seclevel, AuthProto=param.authproto, AuthPass=param.authpass, PrivProto=param.privproto, PrivPass=param.privpass, SecName=param.username)

# get cpu usage
string = netsnmp.VarList('hypervisorCpuUsagePercent')
vars = session.walk(string)
cpuusage = 0
for i in vars:
    cpuusage = cpuusage + int(i)
cpuusage = cpuusage / len(vars)

# get mem usage
string = netsnmp.VarList('hypervisorMemoryUsagePercent')
vars = session.walk(string)
memusage = 0
for i in vars:
    memusage = memusage + int(i)
memusage = memusage / len(vars)

# get vmcount
string = netsnmp.VarList('hypervisorVmCount')
vars = session.walk(string)
vmcount = 0
for i in vars:
    vmcount = vmcount + int(i)

if param.zabbix:
    zabbix_api = ZabbixAPI(url='http://'+param.zabbix_server+'/zabbix/', user=param.zabbix_user, password=param.zabbix_pass)
    zabbix_key = re.sub('\..*$', '', re.sub('^.*/', r'', sys.argv[0]))
    zabbix_key = 'cluster'
    #result = zapi.host.get(status=1)
    #hostnames = [host['host'] for host in result]
    #print hostnames
    packet = [
        ZabbixMetric(param.hostname, zabbix_key + 'CpuUsagePercent', cpuusage),
        ZabbixMetric(param.hostname, zabbix_key + 'MemUsagePercent', memusage),
        ZabbixMetric(param.hostname, zabbix_key + 'VmCount', vmcount),
    ]
    result = ZabbixSender(use_config=False).send(packet)
    if param.isdebug:
        print result
        #print zabbix_key
	#print cpuusage
	#print vmcount

sys.exit(0)
