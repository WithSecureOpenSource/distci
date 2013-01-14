#!/bin/sh

if [ -f /etc/init.d/distci-frontend ]
then
    /etc/init.d/distci-frontend stop
fi

if [ -f /etc/init.d/nginx ]
then
    /etc/init.d/nginx stop
fi

apt-get -y install python-setuptools python-flup nginx python-zookeeper
easy_install /root/deploy/frontend/eggs/distci-*.egg

/etc/init.d/nginx stop

cp /root/deploy/frontend/distci-frontend.nginx /etc/nginx/sites-available/distci-frontend
ln -f /etc/nginx/sites-available/distci-frontend /etc/nginx/sites-enabled/distci-frontend
rm /etc/nginx/sites-enabled/default

mkdir -p /etc/distci
cp /root/deploy/frontend/distci-frontend.conf /etc/distci/frontend.conf

/etc/init.d/nginx start

mkdir -p /var/lib/distci/frontend/tasks

cp /root/deploy/frontend/distci-frontend.init /etc/init.d/distci-frontend
chmod u+x /etc/init.d/distci-frontend
update-rc.d distci-frontend defaults

/etc/init.d/distci-frontend start

