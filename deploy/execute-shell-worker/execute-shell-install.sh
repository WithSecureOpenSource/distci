#!/bin/sh

if [ -f /etc/init.d/distci-execute-shell-worker ]
then
    /etc/init.d/distci-execute-shell-worker stop
fi

apt-get -y install python-setuptools
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/execute-shell-worker/execute-shell.conf /etc/distci/worker/execute-shell.conf

cp /root/deploy/worker/execute-shell-worker/execute-shell.init /etc/init.d/distci-execute-shell-worker
chmod u+x /etc/init.d/distci-execute-shell-worker
update-rc.d distci-execute-shell-worker defaults

/etc/init.d/distci-execute-shell-worker start

