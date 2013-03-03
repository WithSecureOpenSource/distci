#!/bin/sh

if [ -z "$PONI_ROOT" ]
then
    echo PONI_ROOT environmental variable is not set
    exit 127
fi

if [ -z "$DISTCI_EGGS" ]
then
    echo DISTCI_EGGS environmental variable is not set
    exit 127
fi

if [ -z "$EUCA_URL" ]
then
    echo EUCA_URL environmental variable is not set
    exit 127
fi

if [ -z "$EUCA_ACCESS_KEY" ]
then
    echo EUCA_ACCESS_KEY environmental variable is not set
    exit 127
fi

if [ -z "$EUCA_SECRET_KEY" ]
then
    echo EUCA_SECRET_KEY environmental variable is not set
    exit 127
fi

poni cloud init distci --wait 

poni cloud update distci

poni deploy distci

poni control nodes-prepare setup

poni control zookeeper-setup install

poni control ceph-storage-setup install-stage1
poni control ceph-storage-setup install-stage2
poni control ceph-storage-setup install-stage3

poni control frontend-setup install

poni control calculator-worker-setup install

