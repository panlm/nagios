#!/usr/bin/env python
#from restful_lib import Connection
#conn = Connection(base_url, username="leiming.pan@nutanix.sh", password="nutanix/4u")

import sys
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

if len(sys.argv) != 3:
    print 'Usage: ' + sys.argv[0] + ' clusterip' + ' vmname'
    print
    sys.exit()

clusterip = sys.argv[1]
vm = sys.argv[2]

base_url = "https://" + clusterip + ":9440/PrismGateway/services/rest/v1"

s = requests.Session()
s.auth = ('leiming.pan@nutanix.sh', 'nutanix/4u')

#r = s.get(base_url + '/cluster', verify=False)
#parsed_json = json.loads(r.text)
#print parsed_json['id']
#print parsed_json['name']
#print parsed_json['nameServers'][0]
#print parsed_json['rackableUnits'][0]['model']
#print parsed_json['rackableUnits'][0]['serial']

r = s.get(base_url + '/vms', verify=False)
parsed_json = json.loads(r.text)

i = 0
j = parsed_json['metadata']['count']

while i < j:
    if parsed_json['entities'][i]['vmName'] == vm:
        diskuuid = parsed_json['entities'][i]['nutanixVirtualDiskUuids'][0]
    i = i + 1

r = s.get(base_url + '/virtual_disks/' + diskuuid, verify=False)
parsed_json = json.loads(r.text)

read_mb_2min = parsed_json['stats']['controller.wss_120s_read_MB']
write_mb_2min = parsed_json['stats']['controller.wss_120s_write_MB']
read_mb_1hr = parsed_json['stats']['controller.wss_3600s_read_MB']
write_mb_1hr = parsed_json['stats']['controller.wss_3600s_write_MB']

print 'Read_WSS_in_2mins:' + read_mb_2min,
print 'Write_WSS_in_2mins:' + write_mb_2min,
print 'Read_WSS_in_1hr:' + read_mb_1hr,
print 'Write_WSS_in_1hr:' + write_mb_1hr,
print ' | read_mb_2min=' + read_mb_2min + ';;;;',
print 'write_mb_2min=' + write_mb_2min + ';;;;',
print 'read_mb_1hr=' + read_mb_1hr + ';;;;',
print 'write_mb_1hr=' + write_mb_1hr + ';;;;',

sys.exit()

