#!/bin/sh

if [ -f /etc/init.d/distci-build-control-worker ]
then
    /etc/init.d/distci-build-control-worker stop
fi

apt-get -y install python-setuptools
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/build-control-worker/build-control.conf /etc/distci/worker/build-control.conf

cp /root/deploy/worker/build-control-worker/build-control.init /etc/init.d/distci-build-control-worker
chmod u+x /etc/init.d/distci-build-control-worker
update-rc.d distci-build-control-worker defaults

/etc/init.d/distci-build-control-worker start

