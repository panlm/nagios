#!/usr/bin/env python

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

r = s.get(base_url + '/vms', verify=False)
jsoned = json.loads(r.text)

i = 0
j = jsoned['metadata']['count']

while i < j:
    if jsoned['entities'][i]['vmName'] == vm:
        if jsoned['entities'][i]['powerState'] == 'off':
            print 'VM is poweroff'
            sys.exit()
        #print jsoned['entities'][i]['vmName'],
        #print jsoned['entities'][i]['stats']['controller.storage_tier.ssd.usage_bytes'],
        #print jsoned['entities'][i]['stats']['controller.storage_tier.das-sata.usage_bytes']
        ssd_usage_mb = long(jsoned['entities'][i]['stats']['controller.storage_tier.ssd.usage_bytes']) / 1024 / 1024
        hdd_usage_mb = long(jsoned['entities'][i]['stats']['controller.storage_tier.das-sata.usage_bytes']) / 1024 / 1024
        break
    i = i + 1


print 'ssd_usage_mb:' + str(ssd_usage_mb),
print 'hdd_usage_mb:' + str(hdd_usage_mb),
print ' | ssd_usage_mb=' + str(ssd_usage_mb) + ';;;;',
print 'hdd_usage_mb=' + str(hdd_usage_mb) + ';;;;',

sys.exit()

