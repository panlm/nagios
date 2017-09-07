#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 cluster1_ip username password"
    exit 9
fi

export PATH=$PATH:/usr/local/bin
umask 0000
timestamp=`date +%s`
clusterip=$1
username=$2
password=$3
zabbixserver=127.0.0.1


#CRITICAL WARNING INFO AUDIT
for i in CRITICAL WARNING INFO ; do
    out=/tmp/${clusterip}_${i}.out
    curl -kX GET \
      "https://$clusterip:9440/PrismGateway/services/rest/v1/alerts/?resolved=false&severity="$i \
      -H 'cache-control: no-cache' \
      -u "$username:$password" >$out 2>/dev/null
    num=`cat $out |jq -r .metadata.totalEntities`
    zabbix_sender -z $zabbixserver -s $clusterip -k 'clusterAlert'$i -o $num
done

exit

for cluster in $* ; do
    path=`dirname $0`
    timefile=/var/tmp/$cluster-listalert.sh.timestamp
    outfile=/var/tmp/$cluster-listalert.sh.out.$timestamp
    alertfile=/var/tmp/$cluster-listalert.sh.alert.$timestamp
    apifile=$path/api-listalert
    runfile=$path/run-listalert-$cluster

    #get start_time and end_time
    #if no timefile then period is the last hour
    #and get last 100 alerts
    end_time=${timestamp}000000
    if [ -f $timefile ]; then
        start_time=`cat $timefile`
    else
        start_time=`echo $timestamp - 3600 |bc `000000
        count=100
    fi
    
    #Optional Format with csvlook
    #if [ -x /usr/bin/in2csv ]; then
    #    STR=" |jq -s . |in2csv --format json - |csvlook"
    #else
    #    STR=""
    #fi
    
    string1="start_time_in_usecs="$start_time
    string2="end_time_in_usecs="$end_time
    
    cat $apifile >$runfile
    sed -i "/https/s/10\.132\.68\.45/$cluster/" $runfile
    if [ -z $count ]; then
        sed -i "/https/s/alerts\/'/alerts\/?$string1\&$string2'/" $runfile
    else
        sed -i "/https/s/alerts\/'/alerts\/?$string1\&$string2\&count=100'/" $runfile
    fi
    chmod a+x $runfile
    
    #save all alert to tmpfile
    $runfile 2>/dev/null |/usr/local/bin/jq -r '.' >$outfile

    #start prase tmpfile and write to alertfile
    t1=/var/tmp/$$.1
    t2=/var/tmp/$$.2
    i=0
    index=`cat $outfile |jq -r '.metadata.end_index'`
    while [[ $i -lt $index ]]; do
        cat $outfile |jq -r '.entities['"$i"'] | [.context_types, .context_values] | transpose | map( {(.[0]): .[1]} ) | add' >$t1
        cat $outfile |jq -r '.entities['"$i"'] | {alert_type_uuid, created_time_stamp_in_usecs, severity, message}' >$t2
        #get all replacement string, like {container_name} or {remote_site}
        strings=`cat $t2 |grep '"message":' |grep -oE '\{[^}]+\}' |xargs |tr -d '{}'`
        for str in $strings ; do
            result=`cat $t1 |awk -F'"' '/"'"$str"'":/ {print $4}'`
            sed -i '/"message":/s/{'"$str"'}/'"$result"'/' $t2
        done
        i=$((i+1))
        cat $t2 >> $alertfile
    done
    rm -f $t1 $t2

    #send alert mail
    mailfrom=1121415@qq.com
    mailto=1121415@qq.com
    if [ -f $alertfile ]; then
        mailfile=/tmp/mail.$$
        cat >$mailfile <<EOF
From: "nutanix" <$mailfrom>
To: "1121415" <$mailfrom>
Subject: Nutanix Enterprise Alerts Mail in Cluster: $cluster

EOF
        cat $alertfile >>$mailfile
        echo '==========' >>$mailfile
        cat $outfile >>$mailfile

        curl --url 'smtps://smtp.qq.com:465' --ssl-reqd \
            --mail-from "$mailfrom" --mail-rcpt "$mailto" \
            --upload-file $mailfile --user '1121415@qq.com:aewqqdhtyljhbidf' --insecure 2>/dev/null
    fi

    echo $end_time > $timefile
done
    
exit 0






#./$runfile 2>/dev/null |jq -r '.entities[] | select ( .alert_type_uuid == \"LoginInfoAudit\" ) | {alert_type_uuid, created_time_stamp_in_usecs, severity}'



#cmd="./$runfile 2>/dev/null |jq -r '.entities[] | {id, alert_type_uuid, message}' "$STR
#cmd="./$runfile 2>/dev/null |jq -r '.entities[] | {alert_type_uuid, created_time_stamp_in_usecs, severity}' "$STR
#cmd="./$runfile 2>/dev/null |jq -r '.entities[] | select ( .alert_type_uuid == \"LoginInfoAudit\" ) | {alert_type_uuid, created_time_stamp_in_usecs, severity}' "$STR
#eval $cmd
