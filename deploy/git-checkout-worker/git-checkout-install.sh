#!/bin/sh

if [ -f /etc/init.d/distci-git-checkout-worker ]
then
    /etc/init.d/distci-git-checkout-worker stop
fi

apt-get -y install python-setuptools git
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/git-checkout-worker/git-checkout.conf /etc/distci/worker/git-checkout.conf

cp /root/deploy/worker/git-checkout-worker/git-checkout.init /etc/init.d/distci-git-checkout-worker
chmod u+x /etc/init.d/distci-git-checkout-worker
update-rc.d distci-git-checkout-worker defaults

/etc/init.d/distci-git-checkout-worker start

