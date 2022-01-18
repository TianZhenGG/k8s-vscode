#!/bin/bash


read -p "请输入百度网盘数据集地址 如 /dataset/data.tar.gz:" file_path


BaiduPCS-Go d --ow --saveto data  $file_path

echo "文件保存在data目录下"

#解压缩文件
# tar -xvf $HOME/data/$file_name