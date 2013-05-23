#!/bin/sh

if [ -f /etc/supervisor/conf.d/distci-frontend.conf ]
then
    supervisorctl stop distci-frontend
fi

if [ -f /etc/init.d/nginx ]
then
    /etc/init.d/nginx stop
fi

mkdir -p /mnt/data

#set $monitors = [ $n.private.ip for $n in $find("ceph-storage/cnode") ]
if ! grep -q ceph /etc/fstab
then
  echo #echo ','.join($monitors) #:/ /mnt/data ceph defaults >> /etc/fstab
  mount -av
fi

mkdir -p /mnt/data/distci/tasks
mkdir -p /mnt/data/distci/jobs

apt-get -y install python-setuptools gunicorn nginx python-zookeeper supervisor
easy_install /root/deploy/frontend/eggs/distci-*.egg

/etc/init.d/nginx stop

cp /root/deploy/frontend/distci-frontend.nginx /etc/nginx/sites-available/distci-frontend
ln -f /etc/nginx/sites-available/distci-frontend /etc/nginx/sites-enabled/distci-frontend
rm /etc/nginx/sites-enabled/default

/etc/init.d/nginx start

mkdir -p /etc/distci
cp /root/deploy/frontend/distci-frontend.conf /etc/distci/frontend.conf

cp /root/deploy/frontend/distci-frontend.supervisor /etc/supervisor/conf.d/distci-frontend.conf

supervisorctl reload

