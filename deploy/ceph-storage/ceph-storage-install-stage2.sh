#!/bin/sh

#if $node.cindex == '0'

#if $node.cindex == '0'
install -m 0600 /root/deploy/ceph/ceph-setup-key /root/.ssh/id_rsa
#end if

#for $ceph_node in $find("ceph-storage/cnode")
ssh -oStrictHostKeyChecking=no root@$ceph_node.cloud.vm_name true
#end for

mkcephfs -c /etc/ceph/ceph.conf -a
#end if

