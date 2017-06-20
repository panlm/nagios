#!/usr/bin/env python
# snmpwalk -v3 -l authPriv -u nutanix -A '12345678' -a SHA -x AES -X '12345678' 10.132.68.23 .system
# session = netsnmp.Session(DestHost='10.132.68.23', Version=3, SecLevel='authPriv', AuthProto='SHA', AuthPass='12345678', PrivProto='AES', PrivPass='12345678', SecName='nutanix')
# version 1

import sys
import os
import time
import netsnmp
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-v', action="store", dest='snmpversion', default=2, type=int)
parser.add_argument('-H', '--hostname', action="store", dest='hostname', default='localhost')
parser.add_argument('-C', action="store", dest='community', default='public')
parser.add_argument('-p', action="store_true", dest='perfdata', default=False)
parser.add_argument('--debug', action="store_true", dest='isdebug', default=False)
# for snmp v3
parser.add_argument('-u', '--username', action="store", dest='username', default='')
parser.add_argument('-l', action="store", dest='seclevel', default='authPriv')
parser.add_argument('-a', action="store", dest='authproto', default='SHA')
parser.add_argument('-A', action="store", dest='authpass', default='')
parser.add_argument('-x', action="store", dest='privproto', default='AES')
parser.add_argument('-X', action="store", dest='privpass', default='')

results = parser.parse_args()

#print results.hostname
#print results.community
#print results.perfdata

if results.snmpversion == '3':
    if results.username == '' or results.authpass == '' or results.privpass == '':
        print "-u, -A and -X are needed when snmpversion is 3\n"
        sys.exit(1)

uptimeoid = ".1.3.6.1.2.1.1.3.0"

session = netsnmp.Session(DestHost=results.hostname, Version=results.snmpversion, SecLevel=results.seclevel, AuthProto=results.authproto, AuthPass=results.authpass, PrivProto=results.privproto, PrivPass=results.privpass, SecName=results.username)
#vars = netsnmp.VarList(netsnmp.Varbind('sysDescr', '0'))
string = netsnmp.VarList(netsnmp.Varbind(uptimeoid),
                         netsnmp.Varbind('ssCpuRawUser', '0'),
                         netsnmp.Varbind('ssCpuRawSystem', '0'),
                         netsnmp.Varbind('ssCpuRawNice', '0'),
                         netsnmp.Varbind('ssCpuRawIdle', '0'),
                         netsnmp.Varbind('ssCpuRawWait', '0'))

# get current values
vars = session.get(string)
if results.isdebug:
    print vars

# if tmpfile existed, read it as last value. 
# if tmpfile does not existed, save current values as last value, and sleep 10 sec
tmpfile = '/var/tmp/chk_snmpv3_cpu_detail-' + results.hostname
if not os.path.exists(tmpfile):
    last_vars = vars
    if results.isdebug:
        print last_vars
    time.sleep(10)
else:
    f = open(tmpfile,'r')
    last_vars = []
    for line in f:
        last_vars.append(line.strip('\n'))
    if results.isdebug:
        print last_vars
    f.close()

# get newest value (get again)
vars = session.get(string)
if results.isdebug:
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
if results.isdebug:
    print diff_vars

f = open(tmpfile,'w')
for i in vars:
    f.write(i)
    f.write('\n')
f.close()

total = 0
for i in diff_vars:
    total = total + i
if results.isdebug:
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
if results.perfdata:
    print ' | user=%.2f;;;; nice=%.2f;;;; sys=%.2f;;;; idle=%.2f;;;; wait=%.2f;;;;' % (cpu_user, cpu_nice, cpu_sys, cpu_idle, cpu_wait)
else:
    print ''

sys.exit(0)

