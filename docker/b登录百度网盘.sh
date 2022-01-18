#!/bin/bash

read -p "请输入百度网盘账号:" username
read -p "请输入百度网盘密码:" password

BaiduPCS-Go login --username $username --password $password

#bug 验证码会输入多次,第一次随便输入回车，然后查看第二次的链接输入正确的。