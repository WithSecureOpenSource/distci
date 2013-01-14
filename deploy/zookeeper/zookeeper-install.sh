#!/bin/sh

if [ -f /etc/init.d/zookeeper ]
then
    /etc/init.d/zookeeper stop
fi

apt-get -y install zookeeper zookeeperd

/etc/init.d/zookeeper stop

cp /root/deploy/zookeeper/zookeeper.conf /etc/zookeeper/conf/zoo.cfg
cp /root/deploy/zookeeper/zookeeper-myid /etc/zookeeper/conf/myid

/etc/init.d/zookeeper start

