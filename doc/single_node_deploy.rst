======================
Single node deployment
======================

1. First time install
=====================

1.1. Install and configure zookeeper
------------------------------------

1.1.1. Install zookeeper::

    $ sudo apt-get install zookeeper zookeeperd

1.1.2. Edit ``/etc/zookeeper/conf/myid``, for single node installation, you can use index 1.

1.1.3. Edit ``/etc/zookeeper/conf/zoo.cfg``, and fill in node IP address for server.1 entry.

1.1.4. Restart zookeeper::

    $ sudo /etc/init.d/zookeeper restart

1.2. Install and configure DistCI frontend
------------------------------------------

1.2.1. Install dependencies::

    $ sudo apt-get install python-setuptools python-zookeeper gunicorn nginx supervisor

1.2.2. Install DistCI::

    $ sudo easy_install distci-<version>.egg

1.2.3. Create data directory, e.g. ``/data/distci``

1.2.4. Configure frontend by editing creating ``/etc/distci/frontend.conf``::

    {
        "data_directory": "/data/distci",
        "zookeeper_nodes": [ "<ipaddr>:2128" ],
        "task_frontends": [ "http://<ipaddr>/distci/" ]
    }

1.2.5. Drop in DistCI NGINX configuration at ``/etc/nginx/sites-available/distci-frontend``. Create symbolic link to the same file under ``/etc/nginx/sites-enabled/``. You may need to disable the default NGINX configuration. Restart/reload NGINX after configuration change::

    server {
        location /distci/ {
            rewrite         /distci/(.*) /$1 break;
            proxy_pass      http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

1.2.6. Drop in DistCI frontend supervisor config at ``/etc/supervisor/conf.d/distci-frontend.conf``::

    [program:distci-frontend]
    command=/usr/bin/gunicorn -w 4 'distci.frontend:build_frontend_app("/etc/distci/frontend.conf")'
    autostart=true
    autorestart=true

1.2.7. Reload supervisor::

    $ sudo supervisorctl reload

1.3. Install and configure DistCI workers
-----------------------------------------

1.3.1. Install dependencies::

    $ sudo apt-get install python-setuptools git

1.3.2. Install DistCI::

    $ sudo easy_install distci-<version>.egg

1.3.3. Create worker configurations for build-control, git-checkout, execute-shell and publish-artifacts workers under ``/etc/distci/worker/``, e.g. ``/etc/distci/worker/build-control.conf``::

    {
        "frontends": [ "http://<ipaddr>/distci/" ],
        "task_frontends": [ "http://<ipaddr>/distci/" ]
    }

1.3.4. Create supervisor configuration for each of the workers under ``/etc/supervisor/conf.d/``. E.g. build control worker::

    [program:distci-build-control-worker]
    command=/usr/local/bin/distci-build-control-worker -c /etc/distci/worker/build-control.conf

1.3.5. Reload supervisor::

    $ sudo supervisorctl reload

2. Upgrade
==========

2.1. Upgrade DistCI software::

    $ sudo easy_install distci-<version>.egg

2.2. Restart DistCI frontend service::

    $ sudo supervisorctl restart distci-frontend

2.3. Restart DistCI workers::

    $ sudo supervisorctl restart distci-build-control-worker
    $ sudo supervisorctl restart distci-git-checkout-worker
    $ sudo supervisorctl restart distci-execute-shell-worker
    $ sudo supervisorctl restart distci-publish-artifacts-worker

