#!/bin/bash

read -p "请输入新密码:" password

cat<<EOF > ~/.config/code-server/config.yaml
bind-addr: 127.0.0.1:8080
auth: password
password: $password
cert: false
EOF

curl -H "Content-Type: application/json" -X POST -d '{"pod_name":"'$pod_name'"}' "http://192.168.10.102:29999/update"
