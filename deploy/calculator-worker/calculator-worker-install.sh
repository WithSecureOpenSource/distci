#!/bin/sh

if [ -f /etc/init.d/distci-calculator-worker ]
then
    /etc/init.d/distci-calculator-worker stop
fi

apt-get -y install python-setuptools bc
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/distci-calculator-worker.conf /etc/distci/worker/calculator.conf

cp /root/deploy/worker/distci-calculator-worker.init /etc/init.d/distci-calculator-worker
chmod u+x /etc/init.d/distci-calculator-worker
update-rc.d distci-calculator-worker defaults

/etc/init.d/distci-calculator-worker start

