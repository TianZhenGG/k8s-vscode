#!/bin/bash


pod_name=`cat /etc/hostname`
secret=`cat ~/.config/code-server/config.yaml | grep password: | cut -d ' ' -f 2`
num=`echo $pod_name | cut -d '-' -f 2`
num="code-$num"
curl -H "Content-Type: application/json" -X POST -d '{"secret": "'$secret'", "pod_name":"'$pod_name'","num":"'$num'" }' "http://192.168.10.102:29999/remove"
