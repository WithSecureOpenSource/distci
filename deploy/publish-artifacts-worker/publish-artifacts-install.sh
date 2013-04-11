#!/bin/sh

if [ -f /etc/init.d/distci-publish-artifacts-worker ]
then
    /etc/init.d/distci-publish-artifacts-worker stop
fi

apt-get -y install python-setuptools
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/publish-artifacts-worker/publish-artifacts.conf /etc/distci/worker/publish-artifacts.conf

cp /root/deploy/worker/publish-artifacts-worker/publish-artifacts.init /etc/init.d/distci-publish-artifacts-worker
chmod u+x /etc/init.d/distci-publish-artifacts-worker
update-rc.d distci-publish-artifacts-worker defaults

/etc/init.d/distci-publish-artifacts-worker start

