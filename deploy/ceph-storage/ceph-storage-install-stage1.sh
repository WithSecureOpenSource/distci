#!/bin/sh

if [ -f /etc/init.d/ceph ]
then
    /etc/init.d/ceph stop
fi

echo >> /root/.ssh/authorized_keys
cat /root/deploy/ceph/ceph-setup-key.pub >> /root/.ssh/authorized_keys

cp /root/deploy/ceph/apt-ceph-sources /etc/apt/sources.list.d/ceph.list
apt-key add /root/deploy/ceph/ceph-repo-key.asc

apt-get update
apt-get -y install ceph

/etc/init.d/ceph stop

mkdir -p /var/lib/ceph/osd/ceph-$node.cindex
mkdir -p /var/lib/ceph/mon/ceph-$node.cindex
mkdir -p /var/lib/ceph/mds/ceph-$node.cindex

cp /root/deploy/ceph/ceph.conf /etc/ceph/ceph.conf

