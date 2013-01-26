#!/bin/sh

if [ -f /etc/init.d/distci-frontend ]
then
    /etc/init.d/distci-frontend stop
fi

if [ -f /etc/init.d/nginx ]
then
    /etc/init.d/nginx stop
fi

mkdir -p /mnt/data

#set $monitors = [ $n.private.dns for $n in $find("ceph-storage/cnode") ]
if ! grep -q ceph /etc/fstab
then
  echo #echo ','.join($monitors) #:/ /mnt/data ceph defaults >> /etc/fstab
  mount -av
fi

mkdir -p /mnt/data/distci/tasks

apt-get -y install python-setuptools python-flup nginx python-zookeeper
easy_install /root/deploy/frontend/eggs/distci-*.egg

/etc/init.d/nginx stop

cp /root/deploy/frontend/distci-frontend.nginx /etc/nginx/sites-available/distci-frontend
ln -f /etc/nginx/sites-available/distci-frontend /etc/nginx/sites-enabled/distci-frontend
rm /etc/nginx/sites-enabled/default

mkdir -p /etc/distci
cp /root/deploy/frontend/distci-frontend.conf /etc/distci/frontend.conf

/etc/init.d/nginx start

cp /root/deploy/frontend/distci-frontend.init /etc/init.d/distci-frontend
chmod u+x /etc/init.d/distci-frontend
update-rc.d distci-frontend defaults

/etc/init.d/distci-frontend start

