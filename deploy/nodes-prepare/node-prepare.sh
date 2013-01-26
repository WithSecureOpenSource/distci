#!/bin/sh

echo $node.cloud.vm_name > /etc/hostname
hostname $node.cloud.vm_name

cp /root/deploy/common/hosts /etc/hosts

cp /root/deploy/common/apt-wheezy-sources /etc/apt/sources.list
rm /etc/apt/apt.conf.d/02Proxy
apt-get update

