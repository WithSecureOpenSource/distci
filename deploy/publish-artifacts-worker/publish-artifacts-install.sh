#!/bin/sh

if [ -f /etc/supervisor/conf.d/distci-publish-artifacts-worker.conf ]
then
    supervisorctl stop distci-publish-artifacts-worker
fi

apt-get -y install python-setuptools
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/publish-artifacts-worker/publish-artifacts.conf /etc/distci/worker/publish-artifacts.conf

cp /root/deploy/worker/publish-artifacts-worker/publish-artifacts.supervisor /etc/supervisor/conf.d/distci-publish-artifacts-worker.conf

supervisorctl reload

