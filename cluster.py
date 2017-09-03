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
parser.add_argument('--zabbix_server', action="store", dest='zabbix_server', default='10.132.71.160')
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




# if tmpfile existed, read it as last value. 
# if tmpfile does not existed, save current values as last value, and sleep 10 sec
tmpfile = '/var/tmp/' + re.sub('\..*$', '', re.sub('^.*/', r'', sys.argv[0])) + '-' + param.hostname
if not os.path.exists(tmpfile):
    last_vars = vars
    if param.isdebug:
        print last_vars
    time.sleep(10)
else:
    f = open(tmpfile,'r')
    last_vars = []
    for line in f:
        last_vars.append(line.strip('\n'))
    if param.isdebug:
        print last_vars
    f.close()

# get newest value (get again)
vars = session.get(string)
if param.isdebug:
    print "get again"
    print vars

# get diff from newest and last
i=1
diff_vars = []
while i < len(vars):
    a=int(last_vars[i])
    b=int(vars[i])
    # wrap
    if b < a:
        b = b + 4294967295 + 1
    diff_vars.append(b - a)
    i = i + 1
if param.isdebug:
    print diff_vars

f = open(tmpfile,'w')
for i in vars:
    f.write(i)
    f.write('\n')
f.close()
if os.geteuid() == stat(tmpfile).st_uid:
    os.chmod(tmpfile,0o0666)

total = 0
for i in diff_vars:
    total = total + i
if param.isdebug:
    print "total:%s\n" % (total)

# prevent you run this script too fast.
if total != 0:
    cpu_user = float(diff_vars[0]) / total * 100
    cpu_sys  = float(diff_vars[1]) / total * 100
    cpu_nice = float(diff_vars[2]) / total * 100
    cpu_idle = float(diff_vars[3]) / total * 100
    cpu_wait = float(diff_vars[4]) / total * 100
else:
    cpu_user = 0
    cpu_sys  = 0
    cpu_nice = 0
    cpu_idle = 0
    cpu_wait = 0

print 'user:%.2f nice:%.2f sys:%.2f idle:%.2f wait:%.2f' % (cpu_user, cpu_nice, cpu_sys, cpu_idle, cpu_wait), 
if param.perfdata:
    print ' | user=%.2f;;;; nice=%.2f;;;; sys=%.2f;;;; idle=%.2f;;;; wait=%.2f;;;;' % (cpu_user, cpu_nice, cpu_sys, cpu_idle, cpu_wait)
else:
    print ''

sys.exit(0)

