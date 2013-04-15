#!/bin/sh

if [ -f /etc/supervisor/conf.d/distci-build-control-worker.conf ]
then
    supervisorctl stop distci-build-control-worker
fi

apt-get -y install python-setuptools supervisor
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/build-control-worker/build-control.conf /etc/distci/worker/build-control.conf

cp /root/deploy/worker/build-control-worker/build-control.supervisor /etc/supervisor/conf.d/distci-build-control-worker.conf

supervisorctl reload

