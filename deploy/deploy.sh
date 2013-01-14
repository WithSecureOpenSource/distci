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

poni cloud init distci --wait 

poni deploy distci

poni control nodes-prepare setup

poni control zookeeper-setup install

poni control frontend-setup install


