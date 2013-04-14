#!/bin/sh

if [ -f /etc/supervisor/conf.d/distci-execute-shell-worker.conf ]
then
    supervisorctl stop distci-execute-shell-worker
fi

apt-get -y install python-setuptools supervisor
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/execute-shell-worker/execute-shell.conf /etc/distci/worker/execute-shell.conf

cp /root/deploy/worker/execute-shell-worker/execute-shell.supervisor /etc/supervisor/conf.d/distci-execute-shell-worker.conf

supervisorctl reload

