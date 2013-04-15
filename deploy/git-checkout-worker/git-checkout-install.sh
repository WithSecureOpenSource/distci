#!/bin/sh

if [ -f /etc/supervisor/conf.d/distci-git-checkout-worker.conf ]
then
    supervisorctl stop distci-git-checkout-worker
fi

apt-get -y install python-setuptools supervisor git
easy_install /root/deploy/worker/eggs/distci-*.egg

mkdir -p /etc/distci/worker
cp /root/deploy/worker/git-checkout-worker/git-checkout.conf /etc/distci/worker/git-checkout.conf

cp /root/deploy/worker/git-checkout-worker/git-checkout.supervisor /etc/supervisor/conf.d/distci-git-checkout-worker.conf

supervisorctl reload

