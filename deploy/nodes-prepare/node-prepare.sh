#!/bin/sh

cp /root/deploy/common/apt-wheezy-sources /etc/apt/sources.list
rm /etc/apt/apt.conf.d/02Proxy
apt-get update

