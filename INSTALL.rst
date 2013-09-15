===================
DistCI installation
===================

These instructions have been developep against Debian 7 setup.

Build DistCI package
====================

Building DistCI depends on:
  - make
  - git
  - python-setuptools

Build DistCI Python Egg package:

$ make dist

Development setup
=================

Local development and testing can be conducted without Ceph and/or ZooKeeper, utilizing local disk for both storage and locking functionality.

Frontend
--------

1. Install DistCI dependencies:

  - python-setuptools
  - python-webob
  - nginx
  - gunicorn
  - supervisor

2. Install DistCI::

    $ sudo easy_install distci-<version>.egg

3. Configure frontend by creating ``/etc/distci/frontend.conf``::

    {
        "data_directory": "/srv/distci",
        "task_frontends": [ "http://distci-ipaddr/distci/" ]
    }

4. Create DistCI data directories::

    $ sudo mkdir -p /srv/distci/jobs
    $ sudo mkdir -p /srv/distci/tasks

5. Drop in DistCI NGINX configuration at ``/etc/nginx/sites-available/distci-frontend``. Create symbolic link to the same file under ``/etc/nginx/sites-enabled/``. You may need to disable the default NGINX configuration. Restart/reload NGINX after configuration change::

    server {
        location = /distci/ {
                return 301 /distci/ui/;
        }

        location /distci/ {
            rewrite         /distci/(.*) /$1 break;
            proxy_pass      http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

6. Drop in DistCI frontend supervisor config at ``/etc/supervisor/conf.d/distci-frontend.conf``::

    [program:distci-frontend]
    command=/usr/bin/gunicorn -w 1 'distci.frontend:build_frontend_app("/etc/distci/frontend.conf")'
    autostart=true
    autorestart=true

7. Reload supervisor::

    $ sudo supervisorctl reload

Workers
-------

The current list of workers is:

  - distci-build-control-worker
  - distci-git-checkout-worker
  - distci-execute-shell-worker
  - distci-publish-artifacts-worker
  - distci-copy-artifacts-worker

1. DistCI workers dependencies vary from worker to worker, this set covers the all the current workers:

  - python-setuptools
  - supervisor
  - git

2. Install DistCI::

    $ sudo easy_install distci-<version>.egg

3. For each worker, create configuration file as ``/etc/distci/worker/build-control.conf``::

    {
        "frontends": [ "http://distci-ipaddr/distci/" ]
        "task_frontends": [ "http://distci-ipaddr/distci/" ]
    }

4. For each worker, drop in supervisor config at ``/etc/supervisor/conf.d/distci-build-control-worker.conf``::

    [program:distci-build-control-worker]
    command=/usr/local/bin/distci-build-control-worker -c /etc/distci/worker/build-control.conf
    autostart=true
    autorestart=true

6. Reload supervisor::

    $ sudo supervisorctl reload

Operational setup
=================

Operational setup requires Ceph and ZooKeeper clusters up and running. With shared storage and synchronization, you can have any number of DistCI frontends.

Frontend
--------

1. Install DistCI dependencies:

  - python-setuptools
  - python-webob
  - python-zookeper
  - ceph
  - python-ceph
  - nginx
  - gunicorn
  - supervisor

2. Install DistCI::

    $ sudo easy_install distci-<version>.egg

3. Configure frontend by creating ``/etc/distci/frontend.conf``::

    {
        "data_directory": "/distci",
        "zookeeper_nodes": [ "zk-ip-address:clientport", "zk2-ip-address:clientport", "zkN-ip-address:clientport" ],
        "ceph_monitors": [ "ceph-mon-ip-address", "ceph-mon2-ip-address", "ceph-monN-ip-address" ],
        "task_frontends": [ "http://distci-fe-ipaddr/distci/", "http://distci-fe2-ipaddr/distci/", "http://distci-feN-ipaddr/distci/" ]
    }

4. Drop in DistCI NGINX configuration at ``/etc/nginx/sites-available/distci-frontend``. Create symbolic link to the same file under ``/etc/nginx/sites-enabled/``. You may need to disable the default NGINX configuration. Restart/reload NGINX after configuration change::

    server {
        location = /distci/ {
                return 301 /distci/ui/;
        }

        location /distci/ {
            rewrite         /distci/(.*) /$1 break;
            proxy_pass      http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

5. Drop in DistCI frontend supervisor config at ``/etc/supervisor/conf.d/distci-frontend.conf``::

    [program:distci-frontend]
    command=/usr/bin/gunicorn -w 4 'distci.frontend:build_frontend_app("/etc/distci/frontend.conf")'
    autostart=true
    autorestart=true

6. Reload supervisor::

    $ sudo supervisorctl reload

