#!/usr/bin/env python
# snmpwalk -v3 -l authPriv -u nutanix -A '12345678' -a SHA -x AES -X '12345678' 10.132.68.23 .system

import netsnmp

session = netsnmp.Session(DestHost='10.132.68.23', Version=3, SecLevel='authPriv', AuthProto='SHA', AuthPass='12345678', PrivProto='AES', PrivPass='12345678', SecName='nutanix')
vars = netsnmp.VarList(netsnmp.Varbind('sysDescr', '0'))
print session.get(vars)

#Out[4]: ('Linux example.com 2.6.32-131.2.1.el6.x86_64 #1 SMP Wed May 18 07:07:37 EDT 2011 x86_64',)


