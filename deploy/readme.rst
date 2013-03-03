DistCI deployment
=================

Setting up
----------

1. Set the following environmental variables:

+-----------------+------------------------------------------+---------------------------------------------+
| Variable        | Description                              | Example                                     |
+=================+==========================================+=============================================+
| PONI_ROOT       | Path for the created Poni repository     | /home/noushe/distci-poni-repository         |
+-----------------+------------------------------------------+---------------------------------------------+
| EUCA_URL        | URL pointing to your Eucalyptus endpoint | http://10.133.16.2:8773/services/Eucalyptus |
+-----------------+------------------------------------------+---------------------------------------------+
| EUCA_ACCESS_KEY | Your Eucalyptus ACCESS token             | 1RS0LGD6PDAGE0GZYNFYY                       |
+-----------------+------------------------------------------+---------------------------------------------+
| EUCA_SECRET_KEY | Your Eucalyptus SECRET token             | M0HhTWLLUV99NOrD27o65pHQkAawjelWQqZCs09H    |
+-----------------+------------------------------------------+---------------------------------------------+
| DISTCI_EGGS     | Path to DistCI distribution files        | /Users/noushe/PGM/personal/distci/dist/     |
+-----------------+------------------------------------------+---------------------------------------------+

2. Modify create_poni_config.sh to your taste:
    - How many frontend nodes you want to deploy?
    - How many zookeeper nodes you want to deploy?
    - Replace Image file to match your Eucalyptus setup.
    - Replace ssh-key with your own copy.

Running deployment
------------------

1. Run the following command in order to create configuration for the deployment:

    ./create_poni_config.sh

2. Run the following command in order to actually provision and install the software components:

    ./deploy.sh

3. Run the following command in order to display the IP addresses for the deployed nodes:

    poni list -p


Cleaning up
-----------

1. Run the following command in order to terminate DistCI instances

    poni cloud terminate distci


